from unittest import TestCase
from wax.mock_api import json_egg


class TestMockApi(TestCase):
    def test_json_egg(self):
        resp_obj = json_egg('name', array=False)
        self.assertEqual(resp_obj, 'name')
        resp_obj = json_egg('name', array=True)
        self.assertEqual(resp_obj, ['name'])

        a = ['name', 'age']
        resp_obj = json_egg(a, array=False)
        self.assertEqual(resp_obj, 'name')
        resp_obj = json_egg(a, array=False)
        self.assertEqual(resp_obj, 'age')

        resp_obj = json_egg(['name', 'age'], array=True)
        self.assertEqual(resp_obj, ['name', 'age'])
        resp_obj = json_egg({'name': 'John'}, array=False)
        self.assertEqual(resp_obj, {'name': 'John'})
        a = ['aa', 'bb', 'cc', 'dd', 'ee']
        b = [3, 2, 1]
        resp_obj = json_egg(a, array=b)
        self.assertEqual(resp_obj, ['aa', 'bb', 'cc'])
        resp_obj = json_egg(a, array=b)
        self.assertEqual(resp_obj, ['dd', 'ee'])
        self.assertEqual(b, [1, 3, 2])
        resp_obj = json_egg(a, array=b)
        self.assertEqual(resp_obj, ['aa'])
        self.assertEqual(a, ['bb', 'cc', 'dd', 'ee', 'aa'])
        self.assertEqual(b, [3, 2, 1])

        a = {'$': {'key': ['name', 'age']}, '$[]': 2}
        resp_obj = json_egg(a, array=False)
        self.assertEqual(resp_obj, {'$': [{'key': 'name'}, {'key': 'age'}]})
        a = {'$': {'key': ['name', 'age']}, '$[]': -2}
        resp_obj = json_egg(a, array=False)
        self.assertEqual(resp_obj, {'$': [{'key': 'age'}, {'key': 'name'}]})