import json
import gzip
import base64
from pathlib import Path


def append(ret_dict, path_obj: Path):
    full_path = str(path_obj)
    if path_obj.is_dir():
        ret_dict[full_path] = 0
    elif path_obj.is_file():
        ret_dict[full_path] = base64.b64encode(gzip.compress(path_obj.read_bytes())).decode()


def inline_zip(paths, out_file: str):
    ret = {}
    for path in paths:
        path_obj = Path(path)
        append(ret, path_obj)
        if path_obj.is_dir():
            for p in path_obj.rglob('*'):
                append(ret, p)
    with open(out_file, 'w') as f:
        f.write('zipped_data = ')
        json.dump(ret, f, indent=2)


def inline_unzip(data):
    for path, content in data.items():
        path_obj = Path(path)
        if content == 0:
            path_obj.mkdir(parents=True, exist_ok=True)
        else:
            buf = gzip.decompress(base64.b64decode(content.encode()))
            with path_obj.open('wb') as f:
                f.write(buf)


if __name__ == '__main__':
    inline_zip(['config.json', 'wax-www', 'script'], 'wax/zip_data.py')