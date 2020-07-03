from typing import Dict, List
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
