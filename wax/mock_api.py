from typing import Tuple, Dict, List
import json
import jsonschema
import base64
import re
from wax.lessweb import Request, Response, BadParamError
from wax.lessweb.utils import re_standardize, eafp
from wax.lessweb.webapi import http_methods, NotFoundError, HttpStatus
from wax.load_config import config
from wax.load_swagger import SwaggerData
from wax.load_func import eval_func, default_func, is_evalable, deep_eval
from wax.service import StateServ
from wax.jsonschema_util import jsonschema_to_json
from wax.pql import apply_schema, PqlRuntimeError


def base64ed(buf: bytes) -> str:
    return base64.standard_b64encode(buf).decode()


def cast_param(param_value: List[str], param_type: str):
    if param_type == 'number':
        return float(param_value[0])
    elif param_type == 'integer':
        return int(param_value[0])
    elif param_type == 'boolean':
        return bool(int(param_value[0]) if param_value[0].isdigit() else param_value[0])
    elif param_type == 'array':
        return param_value
    else:  # e.g. 'string'
        return str(param_value[0])


def opt_number(n):
    try:
        return int(n)
    except:
        try:
            return float(n)
        except:
            return n


def validate(instance, *, schema) -> str:
    try:
        jsonschema.validate(instance=instance, schema=schema, resolver=SwaggerData.resolver, format_checker=jsonschema.draft7_format_checker)
        return ''
    except jsonschema.ValidationError as e:
        return str(e)


class InternalError(Exception):
    pass


def hit_endpoint(realpath: str) -> Tuple[Dict, Dict]:
    """
    :return (endpoint, url_params)
    """
    path = realpath[len(config['mockapi-prefix']):]
    swagger_data = SwaggerData.get()
    for endpoint_path, endpoint in swagger_data['paths'].items():
        if endpoint_path == path:
            return endpoint, {}
    for endpoint_path, endpoint in swagger_data['paths'].items():
        search_ret = re.compile(re_standardize(endpoint_path)).search(path)
        if search_ret:
            return endpoint, search_ret.groupdict()
    raise NotFoundError(methods=[])


def hit_operation(endpoint: Dict, method: str) -> Dict:
    supported_methods = []
    for op_method, operation in endpoint.items():
        op_method = op_method.upper()
        if op_method not in http_methods:
            continue
        supported_methods.append(op_method)
        if op_method == method.upper():
            return operation
    raise NotFoundError(methods=supported_methods)


def check_param_str(param_name, *, param_value, schema) -> None:
    """
    检查通过则return，不通过则返回BadParamError
    """
    error_message = validate(param_value, schema=schema)
    if error_message:
        param_value = opt_number(param_value)
        if validate(param_value, schema=schema):
            raise BadParamError(param=param_name, message=error_message)


def param_check(params: List[Dict], request: Request, url_params: Dict) -> None:
    """
    检查通过则return，不通过则返回BadParamError
    """
    for param_dict in params:
        param_name = param_dict['name']
        param_in = param_dict.get('in', 'query')
        param_required = param_dict.get('required', False)
        if param_in == 'header':
            if not request.contains_header(param_name):
                if param_required:
                    raise BadParamError(param=param_name, message='header param is required')
                else:
                    continue
            param_value = request.get_header(param_name)
        elif param_in == 'cookie':
            if not request.contains_cookie(param_name):
                if param_required:
                    raise BadParamError(param=param_name, message='cookie param is required')
                else:
                    continue
            param_value = request.get_cookie(param_name)
        elif param_in == 'path':
            if param_name not in url_params:
                if param_required:
                    raise BadParamError(param=param_name, message='path param is required')
                else:
                    continue
            param_value = url_params[param_name]
        else:
            query_params = request.param_input.query_input
            if param_name not in query_params:
                if param_required:
                    raise BadParamError(param=param_name, message='query param is required')
                else:
                    continue
            param_value = query_params[param_name][0]
        if not param_dict.get('allowEmptyValue', True) and not param_value:
            raise BadParamError(param=param_name, message='allowEmptyValue is true but param is empty')
        check_param_str(param_name, param_value=param_value, schema=param_dict['schema'])


def body_check(operation: Dict, request: Request) -> None:
    """
    检查通过则return，不通过则返回BadParamError
    """
    content_dict = eafp(lambda: operation['requestBody']['content'], {})
    real_content_type = request.get_content_type().lower()
    for content_key, content_val in content_dict.items():
        if content_key.lower() in real_content_type:
            schema = content_val['schema']
            if request.is_json():
                error_message = validate(request.json_input, schema=schema)
            elif request.is_form():
                form_dict = {key: val[0] for key, val in request.param_input.form_input.items()}
                for key, val in request.file_input.items():
                    form_dict = base64ed(val[0].value)
                error_message = validate(form_dict, schema=schema)
                if not error_message:
                    return
                error_message = validate(
                    {key: opt_number(val) for key, val in form_dict.items()}, schema=schema)
            else:
                error_message = validate(base64ed(request.body_data or b''), schema=schema)
            if error_message:
                raise BadParamError(message=error_message, param='requestBody')
            else:
                return
    raise BadParamError(message='unsupported request content-type', param=real_content_type)


def hit_example(operation: Dict, state) -> Tuple[int, Dict, str]:
    """
    :return (status_code, schema, example_json)
    """
    state_basic = state.basic.get()
    if state_basic:
        state_status_code, state_content_type, state_example_name = state_basic.split(':', 2)
    else:
        state_status_code = state_content_type = state_example_name = ''
    if not operation.get('responses'):
        raise InternalError('responses is empty')
    for status_code, response_val in operation['responses'].items():
        if not state_status_code or state_status_code == status_code:
            for content_key, content_val in response_val['content'].items():
                if not state_content_type or state_content_type == content_key:
                    for example_name, example_val in content_val.get('examples', {}).items():
                        if not state_example_name or state_example_name == example_name:
                            return int(status_code), content_val['schema'], json.dumps(example_val['value'])
                    else:
                        return int(status_code), content_val['schema'], ''
            else:
                raise InternalError('response fail to match content-type')
    else:
        raise InternalError('response fail to match status_code')


def rotate_fetch(arr: List):
    if not arr:
        return None
    ret = arr.pop(0)
    arr.append(ret)
    return ret


def json_egg(obj, *, array):
    """
    array is False:
      basic -> basic
      list -> list[0], rotate(list, 1)
      dict -> {key: json_egg(val)}
    array is True:
      list -> list
      some -> [some]
    array is None:
      None
    array == 0:
      []
    array > 0:
      list -> list[:n], rotate(list, n)
      some -> [some] * n
    array < 0:
      list -> list[n-1:-1:-1]
      some -> [some] * (-n)
    array is list:
      n := list[0], rotate(array, 1)
      assert n is (int | None)
      list -> json_egg(list, array=n)
    """
    if array is False:
        if isinstance(obj, list):
            return rotate_fetch(obj)
        elif isinstance(obj, dict):
            ret = {}
            for key, val in obj.items():
                if '[]' in key: continue
                dual_key = key + '[]'
                if dual_key in obj:
                    ret[key] = json_egg(val, array=obj[dual_key])
                else:
                    ret[key] = json_egg(val, array=False)
            return ret
        else:
            return obj
    elif array is True:
        if isinstance(obj, list):
            return obj
        else:
            return [obj]
    elif isinstance(array, int) and array is None:
        return None
    elif isinstance(array, int) and array == 0:
        return []
    elif isinstance(array, int) and array > 0:
        if isinstance(obj, list):
            return [rotate_fetch(obj) for _ in range(array)]
        else:
            return [json_egg(obj, array=False) for _ in range(array)]
    elif isinstance(array, int) and array < 0:
        if isinstance(obj, list):
            ret = [rotate_fetch(obj) for _ in range(-array)]
        else:
            ret = [json_egg(obj, array=False) for _ in range(-array)]
        return ret.reverse() or ret
    elif isinstance(array, list):
        if not array:
            return None
        n = rotate_fetch(array)
        if not (n is None or (isinstance(n, int) and n >= 0)):
            raise InternalError(f'Invalid example: {n} in {array}')
        return json_egg(obj, array=n)
    else:
        raise InternalError(f'Invalid example: {array}')


def chain_filter(func_chain: List[str], resp_obj, request, response, state):
    for func_item in func_chain:
        if is_evalable(func_item):
            func = deep_eval(func_item, request=request, response=response, state=state)
        elif func_item.startswith('@'):
            func = default_func(func_item, request=request, response=response, state=state)
        else:
            func = eval_func(func_item, request=request, response=response, state=state)
        resp_obj = func(resp_obj)
    return resp_obj


def response_check(schema, resp_obj) -> None:
    """
    检查通过则return，不通过则返回InternalError
    """
    error_message = validate(resp_obj, schema=schema)
    if error_message:
        error_message += '\n\n-----------------\nresponse:\n'
        try:
            error_message += json.dumps(resp_obj, ensure_ascii=False)
        except:
            error_message += str(schema)
        raise InternalError(error_message)


def mock_dealer(request: Request, response: Response, state: StateServ):
    try:
        endpoint, url_params = hit_endpoint(request.path)
        request.param_input.url_input.update(url_params)
        if 'parameters' in endpoint:
            param_check(endpoint['parameters'], request=request, url_params=url_params)
        operation = hit_operation(endpoint, method=request.method)
        params = operation.get('parameters', [])
        param_check(params, request=request, url_params=url_params)
        if operation.get('requestBody'):
            body_check(operation, request=request)
        state.operation_id = operation['operationId']
        status_code, schema, example_json = hit_example(operation, state=state)
        if example_json == '':  # 没有example时产生默认的json
            if status_code != 200:
                response.set_status(HttpStatus.of(status_code))
            return jsonschema_to_json('$', schema, SwaggerData.get())
        example = json.loads(example_json)
        # 准备pql的上下文环境
        if request.is_json():
            req_body = request.json_input
        elif request.is_form():
            req_body = {}
            try:
                property_dict = operation['requestBody']['content'].popitem()[-1]['schema']['properties']
                for param_name, param_prop in property_dict.items():
                    if param_name in request.param_input.form_input:
                        req_body[param_name] = cast_param(request.param_input.form_input[param_name], param_prop.get('type', ''))
            except:
                pass
        else:
            req_body = request.body_data
        req_query, req_path, req_header = {}, {}, {}
        for param in endpoint.get('parameters', []) + params:
            param_name = param.get('name')
            if not param_name:
                continue
            param_type = eafp(lambda: param['schema']['type'], '')
            if param.get('in') == 'path':
                if param_name in request.param_input.url_input:
                    req_path[param_name] = cast_param([request.param_input.url_input[param_name]], param_type)
            elif param.get('in') == 'header':
                header_value = request.get_header(param_name)
                if header_value is not None:
                    req_header[param_name] = cast_param([header_value], param_type)
            else:
                if param_name in request.param_input.query_input:
                    req_query[param_name] = cast_param(request.param_input.query_input[param_name], param_type)
        env = {
            'body': req_body,
            'query': req_query,
            'path': req_path,
            'header': req_header,
        }
        resp_obj = apply_schema(env, dict_schema=example)
        response_check(schema=schema, resp_obj=resp_obj)
        if status_code != 200:
            response.set_status(HttpStatus.of(status_code))
        return resp_obj
    except (InternalError, PqlRuntimeError) as e:
        response.send_content_type(mimekey='txt', encoding='utf-8')
        response.set_status(HttpStatus.InternalServerError)
        return str(e)


def pql_playground(query: dict, path: dict, header: dict, body: dict, schema: dict):
    env = {
        "query": query,
        "path": path,
        "header": header,
        "body": body,
    }
    try:
        resp_obj = apply_schema(env, dict_schema=schema)
    except Exception as e:
        resp_obj = {'error': str(e), 'type': str(type(e))}
    return resp_obj


def default_json(schema: dict):
    return jsonschema_to_json('$', schema, SwaggerData.get())


def check_entities(request: Request):
    schema = request.json_input['schema']
    entities = request.json_input['entities']
    for entity in entities:
        try:
            response_check(schema, resp_obj=entity)
        except InternalError as e:
            return {'code': 1, 'message': str(e)}
    return {'code': 0}
