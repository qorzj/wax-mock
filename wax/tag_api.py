from typing import Dict, List
from mako.template import Template  # type: ignore
from wax.lessweb import BadParamError
from wax.lessweb.webapi import http_methods
from wax.service import StateServ
from wax.load_config import config
from wax.load_swagger import SwaggerData


def split_tag(tag: str) -> List[str]:
    assert tag
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


def load_tag():
    swagger_data = SwaggerData.get()
    for endpoint_path, endpoint in swagger_data['paths'].items():
        for op_method, operation in endpoint.items():
            if op_method.upper() not in http_methods: continue
            for tag in operation.get('tags', []):
                if not tag:
                    continue
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
                for status_code, response_val in operation['responses'].items():
                    for content_key, content_val in response_val['content'].items():
                        for example_name, _ in content_val.get('examples', {}).items():
                            op.all_example.append(f'{status_code}:{content_key}:{example_name}')
                tag_tree[major_tag][dir_tag][menu_tag].append(op)
                op_index[op.operationId] = op


load_tag()


def operation_list(tag: str=''):
    if not tag and tag_tree:
        tag = list(tag_tree.keys())[0]
    major_tag, dir_tag, menu_tag = split_tag(tag)
    return Template(filename='wax-www/tpl/tag_list_page.mako', input_encoding='utf-8', output_encoding='utf-8').render(
        tag_tree=tag_tree,
        major_tag=major_tag,
        dir_tag=dir_tag,
        menu_tag=menu_tag,
        git_url=config['git-url']
    )


def operation_detail(opId: str, state: StateServ):
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
