import gzip
import base64
from pathlib import Path
import sys


def inline_unzip(data):
    for path, content in data.items():
        path_obj = Path(path)
        if content == 0:
            path_obj.mkdir(parents=True, exist_ok=True)
        else:
            buf = gzip.decompress(base64.b64decode(content.encode()))
            with path_obj.open('wb') as f:
                f.write(buf)


def print_version():
    """
    显示版本
    """
    from wax import __version__
    text = """
    wax-mock version: {}

    """.format(__version__)
    print(text)


def print_help():
    """
    显示帮助文档
    """
    help_text = """wax-mock: 使用OpenAPI3 JSON文件创建mock server
Usage:
    wax [json文件路径]      启动mock server
    wax -v                查看当前版本
    
    """
    print(help_text)


def entrypoint():
    if not sys.version_info[:3] >= (3, 6, 0):
        print('wax-mock已不支持低版本python，请安装python3.6.0+')
        exit(1)
    if len(sys.argv) <= 1 or sys.argv[1] == '-h':
        print_help()
        exit(0)
    if sys.argv[1] == '-v':
        print_version()
        exit(0)
    if Path('config.json').exists():
        from wax.load_swagger import SwaggerData
        from wax.load_config import config
        SwaggerData.init(json_path=sys.argv[1])
        from wax.index import app
        app.run(port=config['port'], staticpath='wax-www/static')
    else:
        confirm = input("是否创建config.json, wax-www和script (y or n) ? ")
        if confirm.lower() not in ['y', 'n', 'yes', 'no']:
            print("请输入 y 或者 n")
            exit(1)
        if confirm.lower() == 'y':
            from wax.zip_data import zipped_data
            inline_unzip(zipped_data)
            print("修改config.json后即可运行wax")
