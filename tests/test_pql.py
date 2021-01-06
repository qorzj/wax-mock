import json
from unittest import TestCase
from wax.pql import apply_schema


class TestPql(TestCase):
    def test_apply_schema(self):
        # test case 1
        schema = {
            "__from__": "pa:Person",
            "children": {
                "__from__": "Person",
                "__filter__": "it['parent']==pa['id']",
            },
            "__filter__": "not it['parent']",
            "__sort__": "it['birthday']"
        }
        ret = apply_schema(env={}, dict_schema=schema)
        print(json.dumps(ret, ensure_ascii=False, indent=2))
        # test case 2
        schema = {
            "__from__": "ch:Person",
            "__filter__": "it['parent']",
            "__reverse__": True,
            "**pa": {
                "__from__": "Person",
                "__filter__": "it['id']==ch['parent']",
                "__only__": ["id", "name"],
                "__item__": [0],
            }
        }
        ret = apply_schema(env={}, dict_schema=schema)
        print(json.dumps(ret, ensure_ascii=False, indent=2))
        # test case 3
        schema = {
            "all": {
                "__from__": "ch:Person",
                "__reverse__": True,
                "parentId": "-1",
                "parentName": "''",
                "**parent_": {
                    "__from__": "Person",
                    "__filter__": "it['id']==ch['parent']",
                    "__only__": ["id", "name"],
                    "__item__": [0],
                },
            },
            "start": "(page-1)*limit",
            "total": "len(it['all'])",
            "list": "it['all'][it['start']:][:limit]",
            "__except__": ["all"],
            "__item__": [0],
        }
        ret = apply_schema(env={'page': 1, 'limit': 10}, dict_schema=schema)
        print(json.dumps(ret, ensure_ascii=False, indent=2))
        # test case 4
        schema = {
            "all": {
                "__from__": "ch:Person",
                "__reverse__": True,
                "parentId": "-1",
                "parentName": "''",
                "**parent_": {
                    "__from__": "Person",
                    "__filter__": "it['id']==ch['parent']",
                    "__only__": ["id", "name"],
                    "__item__": [0],
                },
            },
            "__helper__": "page",
        }
        ret = apply_schema(env={'query': {'limit': '3', 'page': '1'}}, dict_schema=schema)
        print(json.dumps(ret, ensure_ascii=False, indent=2))
