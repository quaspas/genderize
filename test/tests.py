import os
import re
from unittest.case import TestCase
import httpretty

import xlwt

from genderize import Client, Genderize


class TestMixin(TestCase):
    path = os.path.dirname(os.path.realpath(__file__))
    test_file = 'test.xls'

    def _write(self):
        data = [
                   ['daniel', ''],
                   ['cristina', ''],
                   ['cassandra', ''],
               ] * 3
        workbook = xlwt.Workbook()
        write_sheet = workbook.add_sheet("Sheet1", cell_overwrite_ok=True)
        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                write_sheet.write(y, x, cell)
        workbook.save('{}/{}'.format(self.path, self.test_file))

    def setUp(self):
        self._write()
        self.args = {
            'read_col': 0,
            'write_col': False,
            'min_probability': 95,
            'file': 'test/test.xls'

        }

    def tearDown(self):
        os.remove('{}/{}'.format(self.path, self.test_file))


class TestAPiClient(TestCase):
    params = {
        'name[0]': 'daniel',
        'name[1]': 'cristina',
        'name[2]': 'cassandra'
    }

    # 200 - OK
    response_200 = '[{"name": "daniel", "gender": "male", "probability": "1.00", "count": 796},' \
                   '{"name": "cristina", "gender": "female", "probability": "0.94", "count": 70},' \
                   '{"name": "cassandra", "gender": "female", "probability": "0.63", "count": 39}]'
    # 200 - OK gender null
    response_null = '[{"name": "peter", "gender": "male", "probability": "1.00", "count": 796},' \
                    '{"hippopotamus","gender":"null"}]'
    # 400 - Bad Request
    response_400 = '{ "error": "here\'s your problem, dude!" }'
    # 429 - Too Many Requests
    respones_429 = '{ "error": "you need to slow down!" }'
    # 500 - Internal Server Error
    response_500 = '{ "error": "sorry, my bad!" }'


    @httpretty.activate
    def test_client_errors(self):
        httpretty.register_uri(
            httpretty.GET,
            re.compile("http:\/\/api\.genderize\.io\/.*$"),
            body=self.response_200,
            content_type="application/json"
        )
        res = Client().curl('GET', self.params)
        self.assertEqual(res.status, 200)


class TestRead(TestMixin, TestAPiClient):

    @httpretty.activate
    def test_(self):
        httpretty.register_uri(
            httpretty.GET,
            re.compile("http:\/\/api\.genderize\.io\/.*$"),
            body=self.response_200,
            content_type="application/json"
        )
        gen = Genderize(self.args)
        gen.chunk_size = 3
        data = gen.read()
        print data


class TestWrite(TestMixin):
    pass

