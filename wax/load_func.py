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


default_fn = {}
lib_path = Path('script')


def default_func(func_name: str, **inject) -> Callable:
    lambda_func = (lib_path / f'{func_name}.py').read_text(encoding='utf-8').strip()
    return eval_func(lambda_func, **inject)
