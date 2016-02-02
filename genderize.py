# coding: utf-8
import csv
import argparse
import json
import collections
from time import sleep
import sqlite3

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

    API_KEY = ''
    SCHEME = 'http'
    HOST = 'api.genderize.io'

    def curl(self, method, params=None):
        url = '{scheme}://{host}'.format(scheme=self.SCHEME, host=self.HOST)
        params = params or {}
        if self.API_KEY:
            params['apikey'] = self.API_KEY
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
        help='Path to the .csv file to be read. It will not be overwritten.'
    )
    return vars(parser.parse_args())


_CACHE = {}


def clean_probability(p):
    if not p:
        return 0
    p = p.replace('.','')
    p = p if isinstance(p, int) else int(p)
    return p


def setup_db():
    conn = sqlite3.connect('genderize.db')
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE names(name text, gender text, probability real)''')
    except sqlite3.OperationalError as e:
        print e
    return conn


class Database(object):

    def __init__(self):
        self.conn = setup_db()

    def insert_name(self, name, gender, probability):
        name = name.lower()
        gender = gender.lower()
        probability = clean_probability(probability)
        existing_name = self.fetch(name)
        if not existing_name:
            c = self.conn.cursor()
            c.execute("INSERT INTO names VALUES (?,?,?)", (name, gender, probability,))
            self.conn.commit()

    def fetch(self, name):
        c = self.conn.cursor()
        c.execute('SELECT * FROM names WHERE name=?', (name.lower(),))
        return c.fetchone()

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


def build_names_params(name, params):
    n = len(params)
    key = 'name[{}]'.format(n)
    params[key] = name
    return params


def build_name_param(name):
    return {'name': name.lower()}


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
    db = Database()
    client = Client()
    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, dialect=csv.excel_tab)
        name_col = find_name_column(reader.next())
        for row in reader:
            name = row[0].split(',')[name_col].lower()
            in_db = db.fetch(name)
            if in_db:
                continue
            params = build_name_param(name)
            response = client.curl('get', params=params)
            print reader.line_num, response.content
            n, g, p = interpret_result(response.content)
            db.insert_name(n, g, p)

if __name__ == '__main__':
    run()
