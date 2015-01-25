# coding: utf-8
from collections import OrderedDict
import os
import argparse
import json
import collections
import datetime
from sys import stdout
from time import sleep
from os.path import basename

from requests.exceptions import ConnectionError
import xlwt
from xlrd import open_workbook
from requests.models import Request
from requests.sessions import Session


# NAME_COLUMN: the column in the excel sheet that hold the name to be read
# 0 = column A, 1 = column B, etc.
NAME_COLUMN = 1

# PROBABILITY: The minimum probability needed to assign a gender
# an integer from 0 to 100
PROBABILITY = 95

# WRITE_COLUMN: the column that results will be written in (male as M and female as F)
# 0 = column A, 1 = column B, etc.
WRITE_COLUMN = 13


def timed(method):
    def wrapper(*args, **kw):
        start = datetime.datetime.now()
        result = method(*args, **kw)
        stop = datetime.datetime.now()
        time = (stop - start).seconds
        print '\tCompleted: {} Time: {} seconds'.format(method.__name__, time)
        return result
    return wrapper


class Response(collections.Sequence):

    def __init__(self, response):
        self.response = response
        content = response.content.decode('utf-8')
        self.content = json.loads(content)

    def __len__(self):
        return len(self.content)

    def __getitem__(self, index):
        return self.content[index]


_CACHE = {}


class Client(object):

    SCHEME = 'http'
    HOST = 'api.genderize.io'

    def curl(self, method, params=None):
        url = '{scheme}://{host}'.format(scheme=self.SCHEME, host=self.HOST)
        params = params or {}
        session = Session()
        request = Request(method, url, params=params)
        request = request.prepare()
        while True:
            response = session.send(request)
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                stdout.write('\n')
                print response.content
                sleep(5)
        return Response(response)


def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--file', dest='file', required=True, help='')
    return vars(parser.parse_args())


@timed
def run(args):

    print '-'*80
    print 'Reading'
    print '-'*80

    # read

    client = Client()
    read_file = os.path.join(os.path.dirname(__file__), '', args['file'])
    read_sheet = open_workbook(read_file).sheet_by_index(0)
    data = []

    chunck_size = 20
    sheet_rows = read_sheet.nrows
    chunks = (sheet_rows / chunck_size) + (sheet_rows % chunck_size)

    for chunk in xrange(chunks):
        params = OrderedDict()
        for chunk_item in xrange(chunck_size):
            row_num = (chunk * chunck_size) + chunk_item
            if row_num > sheet_rows:
                break

            name = read_sheet.row(row_num)[NAME_COLUMN].value.lower()
            params['name[{}]'.format(chunk_item)] = name

        # send request
        try:
            response = client.curl('GET', params)
        except ConnectionError:
            client = Client()
            response = client.curl('GET', params)

        # match request with row
        for chunk_item, res in zip(xrange(chunck_size), response.content):
            current_row = (chunk * chunck_size) + chunk_item
            if current_row > sheet_rows:
                break

            row = []
            for cell in read_sheet.row(current_row):
                if cell.ctype == 5:
                    row.append('')
                else:
                    row.append(str(cell.value).rstrip('.0'))

            if res.get('probability'):
                probability = int(float(res.get('probability'))*100)
            else:
                probability = 0
            if probability > PROBABILITY:
                if not row[WRITE_COLUMN]:
                    row[WRITE_COLUMN] = res.get('gender')[0].upper()

            data.append(row)

        stdout.write('\r\t{} / {}'.format(row_num, read_sheet.nrows))
        stdout.flush()
    stdout.write('\n')

    print '-'*80
    print 'Writing'
    print '-'*80

    workbook = xlwt.Workbook()
    write_sheet = workbook.add_sheet("Sheet1", cell_overwrite_ok=True)

    for y, row in enumerate(data):
        for x, cell in enumerate(row):
            write_sheet.write(y, x, cell)
        stdout.write('\r {} / {}'.format(y, read_sheet.nrows))
        stdout.flush()
    stdout.write('\n')

    workbook.save('{}_genderized.xls'.format(basename(args['file']).split('.')[0]))


if __name__ == '__main__':
    run(parse_args())
