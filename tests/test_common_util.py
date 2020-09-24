from wax.common_util import sorted_dict
from unittest import TestCase
import json


class TestKotlinUtil(TestCase):
    def test_sorted_dict(self):
        data = {'paths': {'cc': 1, 'bb': 2, 'aa': 3}, 'aa': ''}
        data['paths'] @= sorted_dict
        self.assertEqual(json.dumps(data), json.dumps({'paths': {'aa': 3, 'bb': 2, 'cc': 1}, 'aa': ''}))
