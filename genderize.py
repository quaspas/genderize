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
        retries = 0
        while retries < 2:
            response = session.send(request)
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                print response.content
                retries += 1
                print 'going to retry'
                sleep(5)
        return Response(response)


def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument(
        '--file',
        dest='file',
        required=True,
        help='Path to the .xsl file to be read. It will not be overwritten.'
    )
    parser.add_argument(
        '-r', '--read',
        dest='read_col',
        type=int,
        default=1,
        required=False,
        help="""
        The column in the excel sheet that hold the name to be read
        0 = column A, 1 = column B, etc.
        """
    )
    parser.add_argument(
        '-w', '--write',
        dest='write_col',
        default=False,
        type=int,
        required=False,
        help="""
        The column that results will be written into (male as M and female as F).
        0 = column A, 1 = column B, etc.
        If nothing is passed a column will be appended to the end of rows.
        """
    )
    parser.add_argument(
        '-p', '--prob',
        dest='min_probability',
        default=95,
        type=int,
        required=False,
        help="""
        The minimum probability needed to assign a gender. An integer from 0 to 100.
        Default is 95.
        """
    )
    return vars(parser.parse_args())


def open_sheet(file_name):
    read_file = os.path.join(os.path.dirname(__file__), '', file_name)
    sheet = open_workbook(read_file).sheet_by_index(0)
    return sheet

class Genderize():

    def __init__(self, args):
        self.read_col = args['read_col']
        self.write_col = args['write_col']
        self.min_probability = args['min_probability']
        self.file = args['file']
        self.read_sheet = open_sheet(self.file)

    def read(self):
        client = Client()
        data = []
        chunk_size = 110
        sheet_rows = self.read_sheet.nrows
        chunks = (sheet_rows / chunk_size) + (sheet_rows % chunk_size)

        for chunk in xrange(chunks):

            params = OrderedDict()

            for chunk_item in xrange(chunk_size):
                row_num = (chunk * chunk_size) + chunk_item
                if row_num > sheet_rows:
                    break

                try:
                    name = self.read_sheet.row(row_num)[self.read_col].value.lower()
                    params['name[{}]'.format(chunk_item)] = name
                except IndexError:
                    pass

            # send request
            # we are going to catch any error and write whatever we have done.
            try:
                try:
                    response = client.curl('GET', params)
                except ConnectionError:
                    client = Client()
                    response = client.curl('GET', params)
            except:
                print 'failed while at row {}. writing what we got'.format(chunk * chunk_size)
                return data

            # match request with row
            for chunk_item, res in zip(xrange(chunk_size), response.content):
                current_row = (chunk * chunk_size) + chunk_item
                if current_row > sheet_rows:
                    break

                row = []
                for cell in self.read_sheet.row(current_row):
                    if cell.ctype == 5:
                        row.append('')
                    else:
                        row.append(str(cell.value).rstrip('.0'))

                if res.get('probability'):
                    probability = int(float(res.get('probability'))*100)
                else:
                    probability = 0
                if probability >= self.min_probability:
                    if self.write_col:
                        if not row[self.write_col]:
                            row[self.write_col] = res.get('gender')[0].upper()
                    else:
                        row.append(res.get('gender')[0].upper())

                data.append(row)

            stdout.write('\r\t{} / {}'.format(row_num, self.read_sheet.nrows))
            stdout.flush()
        stdout.write('\n')

        return data

    def write(self, data):
        workbook = xlwt.Workbook()
        write_sheet = workbook.add_sheet("Sheet1", cell_overwrite_ok=True)

        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                write_sheet.write(y, x, cell)
            stdout.write('\r {} / {}'.format(y, self.read_sheet.nrows))
            stdout.flush()
        stdout.write('\n')

        workbook.save('{}_genderized.xls'.format(basename(self.file).split('.')[0]))

    @timed
    def run(self):
        print '-'*80
        print 'Reading'
        print '-'*80
        data = self.read()
        print '-'*80
        print 'Writing'
        print '-'*80
        self.write(data)


if __name__ == '__main__':
    genderize = Genderize(parse_args())
    genderize.run()
