# coding: utf-8
import csv
import os
import argparse
import json
import collections
import ntpath
from time import sleep
import datetime

from requests.models import Request
from requests.sessions import Session


class Response(collections.Sequence):

    def __init__(self, response):
        self.response = response
        content = response.content.decode('utf-8')
        self.content = json.loads(content)
        self.status = response.status_code

    def __len__(self):
        return len(self.content)

    def __getitem__(self, index):
        return self.content[index]

    def __iter__(self):
        for content in self.content:
            yield content


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
            else:
                retries += 1
                sleep(1)
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


_CACHE = {}


def check_cache(name):
    return _CACHE.get(name.lower(), None)


def set_cache(name, gender, p):
    _CACHE[name.lower()] = [gender.lower(), p]


def interpret_result(result):
    name = result['name']
    gender = '' if result['gender'] is None else result['gender']
    probability = result.get('probability', 0)
    return name, gender, probability


def set_cache_results_list(results_list):
    for result in results_list:
        name, gender, p = interpret_result(result)
        set_cache(name, gender, p)


def find_name_column(first_row):
    row = first_row[0]
    row = row.lower().split(',')
    for n, header in enumerate(row):
        if 'name' in header and 'last' not in header:
            return n
    print "No 'name' column found."


def next_row(reader):
    try:
        return reader.next(), reader.line_num
    except StopIteration:
        return None, None


def build_params(name, params):
    n = len(params)
    key = 'name[{}]'.format(n)
    params[key] = name
    return params


def map_name_to_row(name, n, mapping):
    if mapping.get(name+'_'):
        map_name_to_row(name+'_'+name, n, mapping)
    mapping[name+'_'] = n
    return mapping


def retrieve_row_with_name(name, mapping):
    for k, v in mapping.items():
        if name+'_' in k:
            return mapping.pop(k)


def pair_results_with_rows(results, mapping):
    assert len(results) == len(mapping), "Results: {} Map: {}".format(len(results), len(mapping))
    pairs = []
    for result in results:
        row = retrieve_row_with_name(result['name'], mapping)
        pairs.append([int(row), interpret_result(result)])
    return pairs


def run():
    args = parse_args()
    file = args['file']
    client = Client()
    RESULTS = {} # {'row_num': ['name', 'gender', 'probability']}

    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, dialect=csv.excel_tab)
        name_col = find_name_column(reader.next())

        # GET https://api.genderize.io/?name[0]=peter&name[1]=lois&name[2]=stevie
        params = {} # build up to 10 name params before query
        name_to_row_map = {}
        try:
            while True:

                if len(params) >= 10:
                    # requests may get rate limited
                    response = client.curl('get', params=params)
                    if response.status != 200:
                        print response.status, response.content
                        break

                    set_cache_results_list(response)

                    pairs = pair_results_with_rows(response, name_to_row_map)
                    for pair in pairs:
                        finished_row, results = pair[0], pair[1]
                        RESULTS[finished_row] = results
                    # clean up for ne params
                    params = {}
                    name_to_row_map = {}

                # read a new row
                row, n = next_row(reader)
                if not row:
                    # requests may get rate limited
                    response = client.curl('get', params=params)
                    if response.status != 200:
                        print response.status, response.content
                        break
                    set_cache_results_list(response)
                    pairs = pair_results_with_rows(response, name_to_row_map)
                    for pair in pairs:
                        finished_row, results = pair[0], pair[1]
                        RESULTS[finished_row] = results
                    break

                name = row[0].split(',')[name_col].lower()
                print n, name

                cached_result = check_cache(name)
                if cached_result is not None:
                    RESULTS[n] = cached_result
                else:
                    build_params(name, params)
                    map_name_to_row(name, n, name_to_row_map)
        except Exception as e:
            # If we fail we still want to write whatever we had
            print e

        # write
        file_name = ntpath.basename(file).rstrip('.csv')
        timestamp = datetime.datetime.now().strftime('%d%m%y-%H%m')
        new_file_name = '{}_{}.csv'.format(file_name, timestamp)
        new_file = os.path.join(os.path.dirname(__file__), new_file_name)
        with open(new_file, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row_num in xrange(2, len(RESULTS) + 1):
                writer.writerow(RESULTS[row_num])


if __name__ == '__main__':
    run()
