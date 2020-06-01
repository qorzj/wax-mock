from functools import partial
from wax.lessweb.plugin.redisplugin import RedisServ
from wax.load_swagger import SwaggerData


def return_str(f):
    def g(*a, **b):
        ret = f(*a, **b)
        if isinstance(ret, bytes):
            return ret.decode()
        return ret
    return g


class PatialRedis:
    def __init__(self, name, redis):
        self._name = name
        self._redis = redis

    def __getattr__(self, method):
        return return_str(partial(getattr(self._redis, method), SwaggerData.redis_prefix + self._name))


class StateServ:
    redis_serv: RedisServ
    operation_id: str = ''

    @property
    def basic(self):  # format: 'statusCode:contentType:exampleName'
        return PatialRedis(name=f'{self.operation_id}::basic', redis=self.redis_serv.redis)

    @property
    def extra(self):
        return PatialRedis(name=f'{self.operation_id}::extra', redis=self.redis_serv.redis)
