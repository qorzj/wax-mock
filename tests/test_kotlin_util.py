from unittest import TestCase
import json
from wax.kotlin_util import properties_to_kclass, kclass_index


swagger_data = {
  "paths": {},
  "components": {
    "schemas": {
      "UserPaged": {
        "title": "UserPaged",
        "type": "object",
        "properties": {
          "page": {
            "type": "integer"
          },
          "size": {
            "type": "integer"
          },
          "list": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/User"
            }
          },
          "hospital": {
            "type": "object",
            "properties": {
              "id": {
                "type": "integer",
                "description": "医院ID"
              },
              "name": {
                "type": "string",
                "description": "医院名称"
              },
              "patients": {
                "type": "object",
                "properties": {
                  "page": {
                    "type": "integer"
                  },
                  "size": {
                    "type": "integer"
                  },
                  "list": {
                    "type": "array",
                    "items": {
                      "$ref": "#/components/schemas/User"
                    }
                  }
                }
              }
            }
          },
          "admin": {
            "$ref": "#/components/schemas/User"
          }
        }
      },
      "User": {
        "title": "User",
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "description": "用户ID"
          },
          "name": {
            "type": "string",
            "description": "真实姓名"
          },
          "birthday": {
            "type": "string",
            "format": "date"
          },
          "tags": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      },
      "CommonPage": {
        "title": "CommonPage",
        "type": "object",
        "properties": {
          "page": {
            "type": "integer"
          },
          "size": {
            "type": "integer"
          },
          "list": {
            "type": "array",
            "items": {
              "type": "object"
            }
          }
        }
      }
    }
  }
}


class TestKotlinUtil(TestCase):
    def test_properties_to_kclass(self):
        for name, schema in swagger_data['components']['schemas'].items():
            properties_to_kclass(schema['properties'], name, swagger_data)
        for kclass in kclass_index.values():
            print(kclass.to_class_impl())
            if kclass.generics:
                print(kclass.to_inherit())
