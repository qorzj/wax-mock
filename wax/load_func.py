from typing import Callable
import importlib
import functools
from wax.lessweb.utils import func_arg_spec
from pathlib import Path


class Importer:
    def __call__(self, package: str):
        return importlib.import_module(package)

    def __getattr__(self, item):
        return importlib.import_module(item)


lib = Importer()


def eval_func(lambda_func: str, **inject) -> Callable:
    kwargs = {}
    fn = eval(lambda_func)
    for arg_name in func_arg_spec(fn):
        if arg_name in inject:
            kwargs[arg_name] = inject[arg_name]
    return functools.partial(fn, **kwargs)


lib_path = Path('script')


def default_func(func_name: str, **inject) -> Callable:
    assert func_name.startswith('@')
    lambda_func = (lib_path / f'{func_name[1:]}.py').read_text(encoding='utf-8').strip()
    return eval_func(lambda_func, **inject)


def is_evalable(obj):
    return isinstance(obj, list) and obj and \
           isinstance(obj[0], str) and obj[0].startswith('@')


def deep_eval(obj, **inject):
    if not is_evalable(obj):
        if isinstance(obj, dict):
            return {key: deep_eval(val) for key, val in obj.items()}
        elif isinstance(obj, list):
            return [deep_eval(item) for item in obj]
        else:
            return obj
    fn = default_func(obj[0], **inject)
    args = [deep_eval(arg) for arg in obj[1:]]
    return fn(*args)
