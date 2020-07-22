from typing import List, Optional, Dict, Union
import json
import re
import hashlib
import base64
from wax.lessweb.webapi import http_methods, BadParamError
from wax.jsonschema_util import jsonschema_from_ref
from wax.load_swagger import parse_operation


def indented(text: str, n=4):
    ret = '\n'.join(' ' * n + line for line in text.splitlines())
    if text.endswith('\n'):
        ret += '\n'
    return ret


def safe_str(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def letter_sign(text: str) -> str:
    """生成base32编码的MD5签名"""
    return base64.b32encode(hashlib.md5(text.encode()).digest()).decode()


def properties_sign(properties: Dict, required: List) -> str:
    core_list = [(key, val.get('format') or val.get('type'), val.get('description') or '')
                 for key, val in properties.items()]
    core_list.sort()
    core_list.extend(sorted(required))
    return letter_sign(json.dumps(core_list, ensure_ascii=False))


def capitalize(text: str) -> str:
    """首字母大写，其他字母不变"""
    return text[0].upper() + text[1:] if text else ''


def make_funcname(opId: str) -> str:
    opId = re.sub("[_/{}\"']", '-', opId)
    ret = ''.join(capitalize(seg) for seg in opId.split('-'))
    return ret[0].lower() + ret[1:]


def make_typename(prefix: str, schema):
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    if not properties:
        prefix = 'Success'
    elif 'pageNum' in properties and 'total' in properties and 'list' in properties:
        prefix = 'CommonPage'
    ret = capitalize(prefix)
    sign = properties_sign(properties, required)
    ret += 'T' + sign[:4].lower()
    return ret + 'Vo'


def jsontype_to_ktype(jsontype: str, *, format: str=None) -> str:
    if jsontype == 'integer':
        if format == 'int64':
            return 'Long'
        else:
            return 'Int'
    elif jsontype == 'string':
        if format == 'date-time':
            return 'LocalDateTime'
        elif format == 'date':
            return 'LocalDate'
        elif format == 'time':
            return 'LocalTime'
        else:
            return 'String'
    elif jsontype == 'number':
        return 'Double'
    elif jsontype == 'boolean':
        return 'Boolean'
    elif jsontype == 'array':
        return 'List'
    elif jsontype == 'object':
        return 'JSONObject'
    else:
        raise NotImplementedError((jsontype, format))


class Kprop:
    name: str
    ktype: str  # 例如：Int, List
    generic: str  # 范型类型名
    notNull: bool
    description: str
    kclass: Optional['Kclass'] = None  # 仅object类型设置kclass
    intMin: Optional[int] = None
    intMax: Optional[int] = None

    def to_ktype(self, type_var='') -> str:
        if self.ktype == 'JSONObject' and self.generic:
            return self.generic
        elif not self.generic:
            return self.ktype
        elif type_var:
            return f'{self.ktype}<{type_var}>'
        else:
            return f'{self.ktype}<{self.generic}>'

    def to_kcode(self, type_var='') -> str:
        real_ktype = self.to_ktype(type_var)
        return ('@NotNull\n' if self.notNull else '') + \
               f"""@Schema(description = {safe_str(self.description)})
var {self.name}: {real_ktype}? = null\n"""


class Kclass:
    typeName: str
    properties: List[Kprop]
    generics: List[str]  # 包含的范型

    def to_inherit(self) -> str:
        assert self.generics
        ret = f'class {self.typeName}{"".join(self.generics)}: {self.typeName}<'
        ret += ', '.join(self.generics)
        ret += '>()\n'
        return ret

    def to_class_impl(self) -> str:
        ret = f'open class {self.typeName}'
        if self.generics:
            ret += '<' + ', '.join(chr(ord('T') + i) for i, _ in enumerate(self.generics)) + '>'
        ret += ' {\n'
        for prop in self.properties:
            ret += indented(prop.to_kcode(type_var='T')) + '\n'
        ret += '}\n'
        return ret


kclass_index: Dict[str, Kclass] = {}  # {sign: Kclass}


def schema_to_kprop(propname: str, schema: Dict, swagger_data) -> Kprop:
    description = schema.get('description', '')
    notNull = False
    kclass = None
    if '$ref' in schema:
        ref_schema = jsonschema_from_ref(schema['$ref'], swagger_data)
        typename = schema['$ref'].rsplit('/', 1)[-1]
        kclass = schema_to_kclass(ref_schema, typename, swagger_data)
        ktype = jsontype_to_ktype('object')
        generic = f'{kclass.typeName}<{", ".join(kclass.generics)}>' if kclass.generics else kclass.typeName
    else:
        types = schema.get('type') or ['string']
        if not isinstance(types, list):
            types = [types]
        if 'array' in types:
            items = schema.get('items', {})
            kprop = schema_to_kprop(propname + 'Item', items, swagger_data)
            ktype = jsontype_to_ktype('array')
            if kprop.generic:
                generic = kprop.generic
            else:
                ktype += '<' + kprop.ktype + '>'
                generic = ''
        elif 'object' in types:
            kclass = schema_to_kclass(schema, make_typename(propname, schema), swagger_data)
            ktype = jsontype_to_ktype('object')
            generic = f'{kclass.typeName}<{", ".join(kclass.generics)}>' if kclass.generics else kclass.typeName
        else:
            ktype = jsontype_to_ktype(schema.get('type'), format=schema.get('format'))
            generic = ''
    kprop = Kprop()
    kprop.name = propname
    kprop.ktype = ktype
    kprop.generic = generic
    kprop.notNull = notNull
    kprop.description = description
    kprop.kclass = kclass
    return kprop


def schema_to_kclass(schema: Dict, typeName, swagger_data) -> Kclass:
    """
    object_type_schema -> properties & required -> kclass
    """
    assert typeName
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    sign = properties_sign(properties, required)
    if sign in kclass_index:
        if typeName in swagger_data['components']['schemas']:
            kclass_index[sign].typeName = typeName
        return kclass_index[sign]
    kclass = Kclass()
    kclass.typeName = typeName
    kclass.properties = []
    kclass.generics = []
    for key, val in properties.items():
        kprop = schema_to_kprop(key, val, swagger_data)
        if key in required:
            kprop.notNull = True
        kclass.properties.append(kprop)
        if kprop.ktype == 'List' and kprop.generic:
            kclass.generics.append(kprop.generic)
    kclass_index[sign] = kclass
    return kclass


def schema_to_votype(name: str, schema: Dict, swagger_data, *, inherit=True) -> str:
    kprop = schema_to_kprop(name, schema, swagger_data)
    if kprop.kclass is not None and kprop.kclass.generics:
        ret = f'{kprop.kclass.typeName}<{", ".join(kprop.kclass.generics)}>'
        if inherit:
            return ''.join(re.sub('[,<>]', '', ret).split())
        else:
            return ret
    else:
        return kprop.to_ktype()


def endpoint_to_kcontroller(path, endpoint, swagger_data) -> str:
    controller_name = capitalize(make_funcname(path))
    ret = f"""@RestController
@Validated
class {controller_name}""" + ' {\n'
    for method, operation in endpoint.items():
        if method.upper() not in http_methods: continue
        parsed_op = parse_operation(swagger_data, endpoint, method)
        op_text = f'@{method.capitalize()}Mapping("{path}")\n'
        op_summary = operation.get('summary', '')
        op_description = operation.get('description', '')
        op_text += f'@Operation(summary = {safe_str(op_summary)}, description = {safe_str(op_description)})\n'
        funcname = make_funcname(operation["operationId"])
        # 打印@ApiResponses注解
        resp_ktype = 'String'
        multiple_resp = False
        resp_lines = []
        for status_code, resp_of_status_code in operation.get('responses', {}).items():
            content_lines = []
            for content_type, resp_of_content in resp_of_status_code.get('content', {}).items():
                type_prefix = funcname + ('Fail' if status_code >= '400' else 'Resp')
                votype = schema_to_votype(type_prefix, resp_of_content['schema'], swagger_data)
                content_lines.append(f'Content(mediaType = "{content_type}", schema = Schema(implementation = {votype}::class))')
                if status_code == '200' and 'application/json' in content_type.lower():
                    resp_ktype = schema_to_votype(type_prefix, resp_of_content['schema'], swagger_data, inherit=False)
                else:
                    multiple_resp = True
            resp_lines.append(f'ApiResponse(responseCode = "{status_code}", content = [{", ".join(content_lines)}])')
        if multiple_resp:
            op_text += '@ApiResponses(value = [\n'
            op_text += indented(',\n'.join(resp_lines)) + '\n])\n'
        # 打印函数定义和参数列表
        op_text += f'fun {funcname}('
        param_lines = []
        for source in ['path', 'query']:
            for item in parsed_op['params'][source]:
                name = item.get('name')
                if not name:
                    raise BadParamError(f'name不能为空', param=f'{path} {method.upper()} {source}')
                description = item.get('description', name)
                ktype = jsontype_to_ktype(item['schema']['type'], format=item['schema'].get('format', ''))
                if not item.get('required'):
                    ktype += '?'
                if source == 'path':
                    param_lines.append(f'@Parameter(description = {safe_str(description)}) @PathVariable {name}: {ktype}')
                elif source == 'query':
                    param_lines.append(f'@Parameter(description = {safe_str(description)}) {name}: {ktype}')
        if parsed_op['requests'] and 'application/json' in operation['requestBody']['content']:
            votype = schema_to_votype(funcname + 'Req', operation['requestBody']['content']['application/json']['schema'], swagger_data, inherit=False)
            param_lines.append(f'@RequestBody vo: {votype}')
        if len(param_lines) > 1:
            op_text += '\n' + indented(',\n'.join(param_lines))
        elif len(param_lines) == 1:
            op_text += param_lines[0]
        op_text += f'): {resp_ktype}?' + ' {\n    return null\n}'
        ret += indented(op_text) + '\n\n'
    return ret + '}\n'


def import_headers():
    return """package com.wax.controller
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.media.Content
import io.swagger.v3.oas.annotations.media.Schema
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import javax.validation.constraints.NotNull
import org.json.JSONObject
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.*\n\n"""