from wax.lessweb import Application, Context
from wax.lessweb.plugin.redisplugin import RedisPlugin
from wax.load_config import config


def allow_cors(ctx: Context):
    ctx.response.send_access_allow()
    return ctx()


app = Application()
app.add_plugin(RedisPlugin(**config['redis']))

app.add_interceptor('.*', method='*', dealer=allow_cors)
app.add_options_mapping('.*', lambda:'')

from wax.mock_api import mock_dealer
wax_api_prefix = config['mockapi-prefix']
app.add_mapping(f'{wax_api_prefix}/.*', method='*', dealer=mock_dealer)

from wax.tag_api import operation_list, operation_detail, operation_edit_state
app.add_get_mapping('/', operation_list)
app.add_get_mapping('/tag/{tag}', operation_list)
app.add_get_mapping('/op/{opId}', operation_detail)
app.add_post_mapping('/op/state', operation_edit_state)
