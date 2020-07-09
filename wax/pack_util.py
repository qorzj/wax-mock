from pathlib import Path
import yaml
import json


def glob_find(ref_path):
    yield from Path(ref_path).glob('*.json')
    yield from Path(ref_path).glob('*.yaml')


def dir_mtime(ref_path):
    return max(p.stat().st_mtime for p in glob_find(ref_path))


def packed(ref_path, title, version):
    """
    ref_path -> packed_swagger_data
    """
    dup_path_keys = set()
    dup_component_keys = set()
    swagger_data = {}
    for p in glob_find(ref_path):
        if p.suffix == '.yaml':
            cur_api = yaml.full_load(p.open('r', encoding='utf-8'))
        else:
            cur_api = json.load(p.open('r', encoding='utf-8'))
        if not swagger_data:
            swagger_data.update(cur_api)
            swagger_data['paths'] = {}
            swagger_data['components'] = {'schemas': {}}
        for key, val in cur_api.get('paths', {}).items():
            if key in swagger_data['paths']:
                dup_path_keys.add(key)
            else:
                swagger_data['paths'][key] = val

        for key, val in cur_api.get('components', {}).get('schemas', {}).items():
            if key in swagger_data['components']['schemas']:
                dup_component_keys.add(key)
            else:
                swagger_data['components']['schemas'][key] = val
    if not swagger_data:
        print('Empty reference directory!')
        exit(1)

    if dup_path_keys or dup_component_keys:
        if dup_path_keys:
            print('Duplicated paths keys:')
            for key in dup_path_keys:
                print('    ' + key)
        if dup_component_keys:
            print('Duplicated components keys:')
            for key in dup_component_keys:
                print('    ' + key)
        print('\nLoad swagger failed!')
        exit(1)

    swagger_data['info']['title'] = title
    swagger_data['info']['version'] = version
    return swagger_data


# def unpack(json_path):
#     """
#     json_path_file -> parts/(api.json|paths|components)
#     """
#     SwaggerData.init(json_path=json_path)
#     Path('parts').mkdir(parents=True, exist_ok=True)
#     Path('parts/paths').mkdir(parents=True, exist_ok=True)
#     Path('parts/components').mkdir(parents=True, exist_ok=True)
#     swagger_data = SwaggerData.get()
#     for filename in sorted(os.listdir('parts/paths')):
#         os.remove(f'parts/paths/{filename}')
#     if 'paths' in swagger_data:
#         for path_key, path_val in swagger_data['paths'].items():
#             filename = path_key.replace('/', '_')
#             content = json.dumps({'key': path_key, 'value': path_val}, ensure_ascii=False, indent=2)
#             with Path(f'parts/paths/{filename}.json').open('w', encoding='utf-8') as f:
#                 f.write(content)
#
#     for filename in sorted(os.listdir('parts/components')):
#         os.remove(f'parts/components/{filename}')
#     if 'components' in swagger_data and 'schemas' in swagger_data['components']:
#         for comp_key, comp_val in swagger_data['components']['schemas'].items():
#             content = json.dumps({'key': comp_key, 'value': comp_val}, ensure_ascii=False, indent=2)
#             with Path(f'parts/components/{comp_key}.json').open('w', encoding='utf-8') as f:
#                 f.write(content)
#
#     swagger_data['paths'] = {}
#     swagger_data['components'] = {}
#     content = json.dumps(swagger_data, ensure_ascii=False, indent=2)
#     with Path(f'parts/api.json').open('w', encoding='utf-8') as f:
#         f.write(content)
#
#
# def pack(json_path):
#     """
#     parts/* -> json_path_file
#     """
#     swagger_data = json.load(open('parts/api.json'))
#     swagger_data.setdefault('paths', {})
#     swagger_data.setdefault('components', {})
#     swagger_data['components'].setdefault('schemas', {})
#     for filename in sorted(os.listdir('parts/paths')):
#         if filename.endswith('.json'):
#             content = json.load(open(f'parts/paths/{filename}'))
#             key, value = content['key'], content['value']
#             swagger_data['paths'][key] = value
#
#     for filename in sorted(os.listdir('parts/components')):
#         if filename.endswith('.json'):
#             content = json.load(open(f'parts/components/{filename}'))
#             key, value = content['key'], content['value']
#             swagger_data['components']['schemas'][key] = value
#
#     with open(json_path, 'w', encoding='utf-8') as fp:
#         json.dump(swagger_data, fp=fp, ensure_ascii=False, indent=2)
