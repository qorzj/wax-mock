from typing import Dict, List, Tuple
import json


def deep_copy(obj):
    return json.loads(json.dumps(obj))


def make_row(level, name, types, description, additional, ref=''):
    return {'level': level, 'name': name, 'types': types, 'description': description, 'additional': additional, 'ref': ref}


def jsonschema_from_ref(ref: str, swagger_data: Dict) -> Dict:
    ret = swagger_data
    for seg in ref.split('/'):
        if not seg or seg == '#': continue
        ret = ret.get(seg, {})
    return ret


def jsonschema_to_rows(parent_level: str, name: str, schema: Dict, swagger_data: Dict) -> List:
    level = f'{parent_level}{name}/'
    additional = deep_copy(schema)
    for key in ['description', '$ref', 'type', 'items', 'properties']:
        additional.pop(key, '')
    description = schema.get('description', '')
    if '$ref' in schema:
        ref_schema = jsonschema_from_ref(schema['$ref'], swagger_data)
        ret = jsonschema_to_rows(parent_level, name, ref_schema, swagger_data)
        ret[0].update({'description': description, 'additional': additional})
        return ret
    types = schema.get('type', [])
    if not isinstance(types, list):
        types = [types]
    if 'array' in types:
        items = schema.get('items', {})
        ret = [make_row(level, name, types, description, additional)]
        if items:
            ret.extend(jsonschema_to_rows(level, '[ ]', items, swagger_data))
        return ret
    elif 'object' in types:
        properties = schema.get('properties', {})
        ret = [make_row(level, name, types, description, additional)]
        for key, val in properties.items():
            ret.extend(jsonschema_to_rows(level, key, val, swagger_data))
        return ret
    else:
        return [make_row(level, name, types, description, additional)]


def compare_json(level, actual, expect) -> List[str]:
    def item_to_pair(item) -> Tuple:
        if isinstance(item, str):
            return item, item
        if 'name' in item and 'in' in item:
            return item['name'], item
        if 'level' in item and 'types' in item:
            return item['level'], item
        if 'rows' in item and 'content_type' in item:
            return item.get('status_code', '') + ':' + item['content_type'], item['rows']
        raise NotImplementedError(item)

    if type(actual) != type(expect):
        return [f'{level} 类型不匹配 actual:{type(actual)} expect:{type(expect)}']
    if isinstance(actual, dict):
        ret = []
        for key in actual.keys() | expect.keys():
            ret.extend(compare_json(f'{level}:{key}', actual[key], expect[key]))
        return ret
    elif isinstance(actual, list):
        actual_dict = dict(item_to_pair(item) for item in actual)
        expect_dict = dict(item_to_pair(item) for item in expect)
        return compare_json(level, actual_dict, expect_dict)
    elif actual != expect:
        return [f'{level} 不一致 actual:{type(actual)} expect:{type(expect)}']
    else:
        return []
