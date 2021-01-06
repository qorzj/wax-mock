"""
## 关键词列表
### 流程关键词(按执行顺序)
- from|name
- 根据key/value依次执行map
- filter
- sort|reverse
- only|except
- rename
- item

### 变量关键词
- it
- query
- path
- header
- body
- lib
- operation
  - `operation('get-file-accessToken').example('ok')`
  - `operation('get-file-accessToken').example()`
"""
from typing import List, Dict, Any
import json
import re
from wax.load_func import lib


KEYWORDS = [
    '__helper__',
    '__from__',
    '__name__',
    '__filter__',
    '__sort__',
    '__reverse__',
    '__only__',
    '__except__',
    '__rename__',
    '__item__',
]


class PqlRuntimeError(Exception):
    def __init__(self, path, reason):
        self.path = path
        self.reason = reason

    def __str__(self):
        return f'{self.path}: {self.reason}'


def is_var_name(name: str) -> bool:
    return bool(re.match(r'^\w+$', name))


def match_name_pair(text: str) -> Any:
    match_ret = re.match(r'^(\w+:)?(\w+)$', text)
    if not match_ret:
        return None, None
    outer_part, inner_part = match_ret.groups()
    if not outer_part:
        return outer_part, inner_part
    else:
        return outer_part[:-1], inner_part


def query_entity(entity_name) -> List:
    try:
        text = open(f'entity/{entity_name}.json').read()
    except:
        raise PqlRuntimeError('', f'数据未创建({entity_name})')
    try:
        data = json.loads(text)
    except:
        raise PqlRuntimeError('', f'数据无法解析JSON({entity_name})')
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise PqlRuntimeError('', f'数据不合法，只支持list[dict]类型({entity_name})')
    return data


def helper_schema(helper_name, dict_schema: Dict) -> Dict:
    try:
        text = open(f'helper/{helper_name}.json').read()
    except:
        raise PqlRuntimeError('__helper__', f'helper未创建({helper_name})')
    try:
        helper_schema = json.loads(text)
    except:
        raise PqlRuntimeError('__helper__', f'helper无法解析JSON({helper_name})')
    if not isinstance(helper_schema, dict):
        raise PqlRuntimeError('__helper__', f'helper不合法，只支持dict类型({helper_name})')
    for key, value in dict_schema.items():
        if key == '__helper__':
            continue
        helper_schema[key] = value
    return helper_schema


def apply_schema(env, dict_schema) -> Any:
    """
    把dict类型的schema实例化为数组类型的rows，或__return__指定的值
    """
    if not isinstance(dict_schema, dict):
        raise PqlRuntimeError('', 'schema必须是dict类型')
    # 处理helper类型的schema
    if '__helper__' in dict_schema:
        filled_schema = helper_schema(helper_name=dict_schema['__helper__'], dict_schema=dict_schema)
        return apply_schema(env, dict_schema=filled_schema)
    filterd_rows = []
    renamed_rows = []
    outer_name, cur_rows = None, [{}]
    # 第一阶段：name|from
    if '__name__' in dict_schema and '__from__' in dict_schema:
        raise PqlRuntimeError('__name__', '__name__和__from__不能同时定义')
    if '__name__' in dict_schema:
        if not is_var_name(dict_schema['__name__']):
            raise PqlRuntimeError('__name__', '语法错误')
        outer_name = dict_schema['__name__']
    elif '__from__' in dict_schema:
        outer_name, inner_name = match_name_pair(dict_schema['__from__'])
        if not inner_name:
            raise PqlRuntimeError('__from__', '语法错误')
        try:
            cur_rows = query_entity(inner_name)
        except PqlRuntimeError as e:
            raise PqlRuntimeError('__from__', e.reason)
    for cur_row in cur_rows:
        env['it'] = cur_row
        if outer_name:
            env[outer_name] = cur_row
        # 第二阶段：根据key/value依次执行map
        for key, func_or_schemas in dict_schema.items():
            if key in KEYWORDS:
                continue
            value = None
            if not isinstance(func_or_schemas, list):
                func_or_schemas = [func_or_schemas]
            for func_or_schema in func_or_schemas:
                if isinstance(func_or_schema, str):
                    if not func_or_schema:
                        raise PqlRuntimeError(key, '语法错误，不支持空字符串')
                    try:
                        value = apply_lambda(env, func=func_or_schema)
                    except SyntaxError as e:
                        raise PqlRuntimeError(key, '语法错误: ' + str(e))
                    except Exception as e:
                        raise PqlRuntimeError(key, f'运行时错误: {type(e)} {e}')
                elif isinstance(func_or_schema, dict):
                    try:
                        value = apply_schema(dict(env), dict_schema=func_or_schema)
                    except PqlRuntimeError as e:
                        raise PqlRuntimeError(f'{key}/{e.path}', e.reason)
                else:
                    raise PqlRuntimeError(key, '语法错误，只支持dict或str类型')
            try:
                cur_row.update(apply_items(key, rows=value))
            except PqlRuntimeError as e:
                raise PqlRuntimeError(f'{key}', e.reason)
        # 第三阶段：filter
        is_chosen = True
        if '__filter__' in dict_schema:
            func = dict_schema['__filter__']
            if not isinstance(func, str):
                raise PqlRuntimeError('__filter__', '语法错误，只支持str类型')
            is_chosen = apply_lambda(env, func)
        if is_chosen:
            filterd_rows.append(cur_row)
    # 第四阶段：sort|reverse
    if '__sort__' in dict_schema and '__reverse__' in dict_schema:
        raise PqlRuntimeError('__sort__', '__sort__和__reverse__不能同时定义')
    if dict_schema.get('__reverse__') is True:
        filterd_rows.reverse()
    elif '__sort__' in dict_schema or '__reverse__' in dict_schema:
        need_reverse = '__reverse__' in dict_schema
        func = dict_schema['__reverse__'] if need_reverse else dict_schema['__sort__']
        filterd_rows.sort(key=lambda it: apply_lambda(dict(env, it=it), func), reverse=need_reverse)
    # 第五阶段：only|except
    only_names, except_names = [], []
    if '__only__' in dict_schema and '__except__' in dict_schema:
        raise PqlRuntimeError('__only__', '__only__和__except__不能同时定义')
    if '__only__' in dict_schema:
        only_names = dict_schema['__only__']
        if not isinstance(only_names, list) or not all(isinstance(name, str) for name in only_names):
            raise PqlRuntimeError('__only__', '语法错误，只支持list[str]类型')
        if not all(is_var_name(name) for name in only_names):
            raise PqlRuntimeError('__only__', '语法错误')
    elif '__except__' in dict_schema:
        except_names = dict_schema['__except__']
        if not isinstance(except_names, list) or not all(isinstance(name, str) for name in except_names):
            raise PqlRuntimeError('__except__', '语法错误，只支持list[str]类型')
        if not all(is_var_name(name) for name in except_names):
            raise PqlRuntimeError('__except__', '语法错误')
    # 第六阶段：rename
    rename_rules = {}
    if '__rename__' in dict_schema:
        rename_pairs = dict_schema['__rename__']
        if not isinstance(rename_pairs, list) or not all(isinstance(name, str) for name in rename_pairs):
            raise PqlRuntimeError('__rename__', '语法错误，只支持list[str]类型')
        for name_pair in rename_pairs:
            outer_name, inner_name = match_name_pair(name_pair)
            if not inner_name or not outer_name:
                raise PqlRuntimeError('__rename__', '语法错误')
            rename_rules[inner_name] = outer_name
    for cur_row in filterd_rows:
        if isinstance(cur_row, dict):
            # 第五阶段：only|except
            if '__only__' in dict_schema:  # 重要，不可省略！
                cur_row = {key: value for (key, value) in cur_row.items() if key in only_names}
            elif '__except__' in dict_schema:
                cur_row = {key: value for (key, value) in cur_row.items() if key not in except_names}
            # 第六阶段：rename
            renamed_row = {}
            for key, value in cur_row.items():
                if key in rename_rules:
                    renamed_row[rename_rules[key]] = value
                else:
                    renamed_row[key] = value
            # 排除结果中的None值
            renamed_row = {key: value for (key, value) in renamed_row.items()
                           if key and value is not None}
            renamed_rows.append(renamed_row)
    # 第七阶段：item
    if '__item__' in dict_schema:
        item_indices = dict_schema['__item__']
        if not isinstance(item_indices, list) or not all(
                indice is None or isinstance(indice, int) for indice in item_indices):
            raise PqlRuntimeError('__return__', '语法错误，只支持list[int?]类型')
        if not 1 <= len(item_indices) <= 3:
            raise PqlRuntimeError('__return__', '语法错误，长度应该在1~3范围内')
        if len(item_indices) == 1 and item_indices[0] is None:
            raise PqlRuntimeError('__return__', '语法错误，单个下标不能为null')
        try:
            if len(item_indices) == 1:
                return renamed_rows[item_indices[0]]
            elif len(item_indices) == 2:
                start, end = item_indices
                return renamed_rows[start:end]
            elif len(item_indices) == 3:
                start, end, step = item_indices
                return renamed_rows[start:end:step]
        except:
            return None
    else:
        return renamed_rows


def apply_items(key: str, rows: Any) -> Dict:
    """
    把(key, rows)变成字典类型的值。
    例如：
    {'name': rows} => {'name': rows}
    {'**name': rows} => {**rows}
    {'**name': rows} => {}  # error! rows is not dict
    {'**name[0]': rows} => {}  # error!
    """
    match_ret = re.match(r'^(\*\*)?(\w+)$', key)
    if not match_ret:
        raise PqlRuntimeError('', 'key语法错误')
    if key.startswith('**'):
        if rows is None:  # {"__item__": [0]}可能返回None
            return {}
        if not isinstance(rows, dict):
            raise PqlRuntimeError('', '运行时错误，值不是dict类型，考虑使用__item__')
        key_prefix = match_ret.groups()[1]
        return {
            (key_prefix + sub_key if key_prefix[-1] == '_' else key_prefix + sub_key[0].upper() + sub_key[1:]): value
            for sub_key, value in rows.items()
        }
    else:
        return {key: rows}


def apply_lambda(env: Dict, func: str) -> Any:
    return eval('lambda %s: %s' % (','.join(env), func))(**env)


