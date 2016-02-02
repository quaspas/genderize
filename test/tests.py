import os
import re
from unittest.case import TestCase

import httpretty

from genderize import Client, set_cache, _CACHE, check_cache, find_name_column, build_names_params, retrieve_row_with_name, \
    map_name_to_row, clean_probability


class TestMixin(TestCase):
    path = os.path.dirname(os.path.realpath(__file__))
    test_file = 'test.xls'
    data = [['name', ],]
    data.extend([['daniel', ], ['cristina', ], ['cassandra', ], ] * 3)

    def _write(self):
        pass

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


class Tests(TestCase):

    def test_set_cache(self):
        set_cache('Ann', 'Female', '1.00')
        self.assertDictContainsSubset({'ann': ['female', '1.00']},_CACHE)

    def test_retrieve_cache(self):
        set_cache('Ann', 'Female', '1.00')
        self.assertIsNotNone(check_cache('Ann'))

    def test_find_header(self):
        actual = find_name_column(['LoadId,Salutation,FirstName,LastName'])
        self.assertEquals(actual, 2)

    def test_find_header_no_name(self):
        actual = find_name_column(['LoadId,Salutation,LastName'])
        self.assertIsNone(actual)

    def test_build_new_params(self):
        params = {}
        actual = build_names_params('ann', params)
        expected = {'name[0]':'ann'}
        self.assertDictContainsSubset(expected, actual)

    def test_add_to_params(self):
        params = {'name[0]':'ann'}
        actual = build_names_params('bob', params)
        expected = {'name[0]':'ann', 'name[1]':'bob'}
        self.assertDictContainsSubset(expected, actual)

    def test_set_row_with_name(self):
        map = {}
        map_name_to_row('a', 1, map)
        map_name_to_row('a', 2, map)
        self.assertEquals(len(map), 2)

    def test_retrieve_row_with_name_dupes(self):
        mapping = {
            'a': '1',
            'aa': '2',
            'aaa': '3',
            'b': '4',
        }
        retrieve_row_with_name('a', mapping)
        self.assertEquals(len(mapping), 3)

    def test_clean_probability_none(self):
        p, expected = None, 0
        actual = clean_probability(p)
        self.assertEquals(actual, expected)

    def test_clean_probability_none(self):
        p, expected = 0, 0
        actual = clean_probability(p)
        self.assertEquals(actual, expected)

    def test_clean_probability_100(self):
        p, expected = '1.00', 100
        actual = clean_probability(p)
        self.assertEquals(actual, expected)

    def test_clean_probability_80(self):
        p, expected = '0.80', 80
        actual = clean_probability(p)
        self.assertEquals(actual, expected)
