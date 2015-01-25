# coding: utf-8
import os
import argparse
import json
import collections
import datetime
from sys import stdout
from time import sleep

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
        self.count = self.content.get('count')
        self.gender = self.content.get('gender')
        if self.content.get('probability'):
            self.probability = int(float(self.content.get('probability'))*100)
        else:
            self.probability = 0

    def __len__(self):
        return len(self.content)

    def __getitem__(self, index):
        return self.content[index]


_CACHE = {}


class Client(object):

    SCHEME = 'http'
    HOST = 'api.genderize.io'

    def curl(self, method, params=None):
        name = params['name'].lower()
        if name in _CACHE:
            return _CACHE[name]
        url = '{scheme}://{host}'.format(scheme=self.SCHEME, host=self.HOST)
        params = params or {}
        session = Session()
        request = Request(method, url, params=params)
        request = request.prepare()
        while True:
            response = session.send(request)
            if response.status_code == 200:
                _CACHE[name] = Response(response)
                break
            elif response.status_code == 429:
                stdout.write('\n')
                print response.content
                sleep(10)
        return Response(response)


def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--filename', dest='filename', required=True, help='')
    return vars(parser.parse_args())


@timed
def run(args):

    print '-'*80
    print 'Reading'
    print '-'*80

    # read

    client = Client()
    read_file = os.path.join(os.path.dirname(__file__), '', args['filename'])
    read_sheet = open_workbook(read_file).sheet_by_index(0)
    data = []

    for row_num in range(10):
    # for row_num in range(read_sheet.nrows):
        name = read_sheet.row(row_num)[NAME_COLUMN].value
        if name:
            params = {'name': name}
            try:
                response = client.curl('GET', params)
            except ConnectionError:
                client = Client()
                response = client.curl('GET', params)
            row = [str(r.value).rstrip('.0') for r in read_sheet.row(row_num)]
            if response.probability >= PROBABILITY:
                row.append(response.gender)
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

    workbook.save('output.xls')


if __name__ == '__main__':
    run(parse_args())
