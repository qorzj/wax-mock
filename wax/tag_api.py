from typing import Dict, List
import itertools
import json
from mako.template import Template  # type: ignore
from wax.lessweb import BadParamError, Context
from wax.lessweb.webapi import http_methods
from wax.service import StateServ
from wax.load_config import config
from wax.load_swagger import SwaggerData, parse_operation
from wax.jsonschema_util import compare_json
from wax.kotlin_util import import_headers, schema_to_kclass, endpoint_to_kcontroller, kclass_index


def split_tag(tag: str) -> List[str]:
    if not tag:
        tag = '其他'
    segs = tag.replace('/', '-').split('-', 2)
    if len(segs) == 1:
        segs.append('API')
    if len(segs) == 2:
        segs.append('API')
    return segs


class Operation:
    method: str
    path: str
    summary: str
    operationId: str
    description: str
    # state
    basic: str
    extra: str
    all_example: List[str]  # List[stateBasic]


# {majorTag: {dirTag: {menuTag: List[Operation]}}}
tag_tree: Dict[str, Dict[str, Dict[str, List[Operation]]]] = {}
op_index: Dict[str, Operation] = {}  # {operationId: Operation}


def first_time_append_op(tag_set, major_tag, op) -> bool:
    tag_set.setdefault(major_tag, set())
    if (op.method, op.path) not in tag_set[major_tag]:
        tag_set[major_tag].add((op.method, op.path))
        return True
    else:
        return False


def load_tag():
    tag_set = {}
    swagger_data = SwaggerData.get()
    for endpoint_path, endpoint in swagger_data['paths'].items():
        for op_method, operation in endpoint.items():
            if op_method.upper() not in http_methods: continue
            for tag in operation.get('tags', []) or ['']:
                major_tag, dir_tag, menu_tag = split_tag(tag)
                tag_tree.setdefault(major_tag, {})
                tag_tree[major_tag].setdefault(dir_tag, {})
                tag_tree[major_tag][dir_tag].setdefault(menu_tag, [])
                op = Operation()
                op.method = op_method.upper()
                op.path = endpoint_path
                op.summary = operation['summary']
                op.operationId = operation['operationId']
                op.description = operation.get('description', '')
                op.all_example = []
                for status_code, response_val in operation.get('responses', {}).items():
                    for content_key, content_val in response_val['content'].items():
                        for example_name, _ in content_val.get('examples', {}).items():
                            op.all_example.append(f'{status_code}:{content_key}:{example_name}')
                tag_tree[major_tag][dir_tag][menu_tag].append(op)
                #
                tag_tree.setdefault('API', {'API': {'API': []}})
                tag_tree[major_tag].setdefault('API', {'API': []})
                if first_time_append_op(tag_set, 'API', op):
                    tag_tree['API']['API']['API'].append(op)
                if first_time_append_op(tag_set, major_tag, op):
                    tag_tree[major_tag]['API']['API'].append(op)
                #
                op_index[op.operationId] = op


load_tag()


def operation_list(tag: str='API'):
    if not tag and tag_tree:
        tag = list(tag_tree.keys())[0]
    major_tag, dir_tag, menu_tag = split_tag(tag)
    return Template(filename='wax-www/tpl/tag_list_page.mako', input_encoding='utf-8', output_encoding='utf-8').render(
        tag_tree=tag_tree,
        major_tag=major_tag,
        dir_tag=dir_tag,
        menu_tag=menu_tag,
        git_url=config['git-url'],
        title=config['title']
    )


def operation_detail(opId: str, show: str=''):
    op = op_index.get(opId)
    swagger_data = SwaggerData.get()
    endpoint = [val for key, val in swagger_data['paths'].items() if key==op.path][0]
    operation = endpoint[op.method.lower()]
    data = {'op': operation, 'path': op.path, 'method': op.method, 'mock_prefix': config['mockapi-prefix']}
    data.update(parse_operation(swagger_data, endpoint, op.method))
    if show == 'json':
        return data
    return Template(filename='wax-www/tpl/op_detail_page.mako', input_encoding='utf-8', output_encoding='utf-8').render(
        tag_tree=tag_tree,
        git_url=config['git-url'],
        **data
    )


def operation_example(opId: str, state: StateServ):
    op = op_index.get(opId)
    if not op:
        raise BadParamError(message='opId不存在', param='opId')
    state.operation_id = opId
    op.basic = state.basic.get()
    op.extra = state.extra.get()
    return op


def operation_edit_state(state: StateServ, opId: str, basic:str='', extra:str=''):
    if opId not in op_index:
        raise BadParamError(message='opId不存在', param='opId')
    state.operation_id = opId
    if basic is not None:
        state.basic.set(basic, ex=86400 * 90)
    if extra is not None:
        state.extra.set(extra, ex=86400 * 90)
    return {}


def compare_swagger(actual: dict) -> List[str]:
    ret = []
    expect = SwaggerData.get()
    actual_paths = actual.get('paths', {})
    for path in actual_paths.keys() | expect['paths'].keys():
        if path not in actual_paths:
            ret.append(f'actual未包含path: {path}')
            continue
        if path not in expect['paths']:
            ret.append(f'expect未包含path: {path}')
            continue
        for method in actual_paths[path].keys() | expect['paths'][path].keys():
            if method.upper() not in http_methods:
                continue
            if method not in actual_paths[path]:
                ret.append(f'actual未包含接口：{method.upper()} {path}')
                continue
            if method not in expect['paths'][path]:
                ret.append(f'expect未包含接口：{method.upper()} {path}')
                continue
            actual_endpoint = actual_paths[path]
            expect_endpoint = expect['paths'][path]
            actual_op = parse_operation(actual, actual_endpoint, method.upper())
            expect_op = parse_operation(expect, expect_endpoint, method.upper())
            ret.extend(compare_json(f'{path}:{method}:parameters', actual_op['params'], expect_op['params'], actual, expect))
            ret.extend(compare_json(
                f'{path}:{method}:requestBody:content',
                actual_endpoint[method].get('requestBody', {}).get('content'),
                expect_endpoint[method].get('requestBody', {}).get('content'),
                actual, expect))
            try:
                actual_endpoint[method]['responses']['200']['content']['application/json'] = actual_endpoint[
                    method]['responses']['200']['content'].pop('*/*')
            except:
                pass
            ret.extend(compare_json(
                f'{path}:{method}:responses',
                actual_endpoint[method].get('responses'),
                expect_endpoint[method].get('responses'),
                actual, expect))
    return ret


def make_kotlin_code(ctx: Context) -> str:
    swagger_data = SwaggerData.get()
    ret = [import_headers()]
    for name, schema in swagger_data['components']['schemas'].items():
        schema_to_kclass(schema, name, swagger_data)
    for path, endpoint in swagger_data['paths'].items():
        ret.append(endpoint_to_kcontroller(path, endpoint, swagger_data))
    for kclass in kclass_index.values():
        ret.append(kclass.to_class_impl())
        if kclass.generics:
            ret.append(kclass.to_inherit())
    ctx.response.send_content_type('txt', encoding='utf-8')
    return '\n'.join(ret)
