from typing import List, Optional, Dict, Union
import json
import hashlib
import base64
from wax.jsonschema_util import jsonschema_from_ref


def indented(text: str, n=4):
    ret = '\n'.join(' ' * n + line for line in text.splitlines())
    if text.endswith('\n'):
        ret += '\n'
    return ret


def letter_sign(text: str) -> str:
    """生成base32编码的MD5签名"""
    return base64.b32encode(hashlib.md5(text.encode()).digest()).decode()


def properties_sign(properties: Dict) -> str:
    core_list = [(key, val.get('format') or val.get('type'), val.get('description'))
                 for key, val in properties.items()]
    core_list.sort()
    return letter_sign(json.dumps(core_list, ensure_ascii=False))


def capitalize(text: str) -> str:
    """首字母大写，其他字母不变"""
    return text[0].upper() + text[1:] if text else ''


def make_typename(prefix: str, properties):
    ret = capitalize(prefix)
    sign = properties_sign(properties)
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
        else:
            return 'String'
    elif jsontype == 'number':
        return 'Double'
    elif jsontype == 'boolean':
        return 'Boolean'
    elif jsontype == 'array':
        return 'List'
    elif jsontype == 'object':
        return 'Any'
    else:
        raise NotImplementedError((jsontype, format))


class Kprop:
    name: str
    ktype: str  # 例如：Int, List<String>, List<*>
    generic: str  # 范型类型名
    notNull: bool
    description: str
    intMin: Optional[int] = None
    intMax: Optional[int] = None

    def to_kcode(self, type_var='') -> str:
        if self.ktype == 'Any' and self.generic:
            real_ktype = self.generic
        elif not self.generic:
            real_ktype = self.ktype
        elif type_var:
            real_ktype = f'{self.ktype}<{type_var}>'
        else:
            real_ktype = f'{self.ktype}<{self.generic}>'
        return f"""@Schema(description = "{self.description}")
var {self.name}: {real_ktype}{'' if self.notNull else '?'} = null\n"""


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
    if '$ref' in schema:
        ref_schema = jsonschema_from_ref(schema['$ref'], swagger_data)
        typename = schema['$ref'].rsplit('/', 1)[-1]
        kclass = properties_to_kclass(ref_schema.get('properties', {}), typename, swagger_data)
        ktype = jsontype_to_ktype('object')
        generic = kclass.typeName
    else:
        types = schema.get('type') or ['string']
        if not isinstance(types, list):
            types = [types]
        if 'array' in types:
            items = schema.get('items', {})
            kprop = schema_to_kprop('[]', items, swagger_data)
            ktype = jsontype_to_ktype('array')
            if kprop.generic:
                generic = kprop.generic
            else:
                ktype += '<' + kprop.ktype + '>'
                generic = ''
        elif 'object' in types:
            properties = schema.get('properties', {})
            kclass = properties_to_kclass(properties, make_typename(propname, properties), swagger_data)
            ktype = jsontype_to_ktype('object')
            generic = kclass.typeName
        else:
            ktype = jsontype_to_ktype(schema.get('type'), format=schema.get('format'))
            generic = ''
    kprop = Kprop()
    kprop.name = propname
    kprop.ktype = ktype
    kprop.generic = generic
    kprop.notNull = notNull
    kprop.description = description
    return kprop


def properties_to_kclass(properties: Dict, typeName, swagger_data) -> Kclass:
    assert typeName
    sign = properties_sign(properties)
    if sign in kclass_index:
        return kclass_index[sign]
    kclass = Kclass()
    kclass.typeName = typeName
    kclass.properties = []
    kclass.generics = []
    for key, val in properties.items():
        kprop = schema_to_kprop(key, val, swagger_data)
        kclass.properties.append(kprop)
        if kprop.ktype == 'List' and kprop.generic:
            kclass.generics.append(kprop.generic)
    kclass_index[sign] = kclass
    return kclass
