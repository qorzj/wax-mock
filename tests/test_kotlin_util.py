from unittest import TestCase
import json
from wax.kotlin_util import schema_to_kclass, kclass_index, endpoint_to_kcontroller


swagger_data = {
  "openapi": "3.0.0",
  "paths": {
    "/simple/{id}": {
      "parameters": [
        {
          "schema": {
            "type": "integer"
          },
          "name": "id",
          "in": "path",
          "required": True,
          "description": "记录ID"
        }
      ],
      "post": {
        "summary": "新建记录",
        "tags": [],
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
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
              },
              "multipart/form-data": {
                "schema": {
                  "type": "string",
                  "format": "binary",
                  "description": "导出内容"
                }
              }
            },
            "headers": {}
          },
          "400": {
            "description": "Bad Request",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "errno": {
                      "type": "integer"
                    },
                    "message": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        },
        "operationId": "post-simple-id",
        "description": "详细描述详细描述",
        "parameters": [
          {
            "schema": {
              "type": "string"
            },
            "in": "query",
            "name": "token",
            "description": "Access Token",
            "required": True
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
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
                  }
                }
              }
            }
          }
        }
      }
    }
  },
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
      }
    }
  }
}


class TestKotlinUtil(TestCase):
    def test_schema_to_kclass_and_kcontroller(self):
        for name, schema in swagger_data['components']['schemas'].items():
            schema_to_kclass(schema, name, swagger_data, cache=False)
        for path, endpoint in swagger_data['paths'].items():
            print(endpoint_to_kcontroller(path, endpoint, swagger_data))
        for kclass in kclass_index.values():
            print(kclass.to_class_impl())
            if kclass.generics:
                print(kclass.to_inherit())