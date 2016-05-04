# coding: utf-8
import csv
import argparse
import json
import collections
from time import sleep
import sqlite3
from datetime import datetime

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
        c.execute(u'CREATE TABLE names(name text, gender text, probability real)')
    except sqlite3.OperationalError as e:
        pass
    return conn


def clean_name(name):
    name = unicode(name, errors='replace')
    name = name.strip(' ')
    return name

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
            c.execute(u'INSERT INTO names VALUES (?,?,?)', (name, gender, probability,))
            self.conn.commit()

    def fetch(self, name):
        c = self.conn.cursor()
        c.execute(u'SELECT * FROM names WHERE name=?', (name.lower(),))
        return c.fetchone()


def interpret_result(result):
    name = result['name']
    gender = '' if result['gender'] is None else result['gender']
    probability = result.get('probability', 0)
    return name, gender, probability


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


def make_csv(file):
    db = Database()
    new_file = 'genderize-{}.csv'.format(datetime.now().strftime('%b%d%y-%s')).lower()
    print '\tcreating {}'.format(new_file)
    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, dialect=csv.excel_tab)
        name_col = find_name_column(reader.next())
        with open(new_file, 'w') as csvfile:
            fieldnames = ['name', 'gender', 'probability']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                name = row[0].split(',')[name_col].lower()
                name = clean_name(name)
                db_result = db.fetch(name)
                if not db_result:
                    continue
                writer.writerow({
                    'name': db_result[0],
                    'gender': db_result[1],
                    'probability': int(db_result[2]),
                })


def run():
    args = parse_args()
    file = args['file']
    db = Database()
    client = Client()
    new_file = 'genderize-{}.csv'.format(datetime.now().strftime('%b%d%y-%s')).lower()
    with open(file, 'rU') as read_csvfile, open(new_file, 'w') as write_csvfile:
        reader = csv.reader(read_csvfile, dialect=csv.excel_tab)
        name_col = find_name_column(reader.next())
        fieldnames = ['name', 'gender', 'probability']
        writer = csv.DictWriter(write_csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            name = row[0].split(',')[name_col].lower()
            name = clean_name(name)
            in_db = db.fetch(name)
            if in_db:
                writer.writerow({
                    'name': in_db[0],
                    'gender': in_db[1],
                    'probability': int(in_db[2]),
                })
                continue
            params = build_name_param(name)
            response = client.curl('get', params=params)
            n, g, p = interpret_result(response.content)
            print('{}, {}, {}, {}'.format(reader.line_num, n, g , p))
            db.insert_name(n, g, p)
            writer.writerow({
                'name': n,
                'gender': g,
                'probability': int(p),
            })
    print '\tcreated {}'.format(new_file)


if __name__ == '__main__':
    run()
