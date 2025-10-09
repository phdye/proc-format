import os

class Path(str):
    def __new__(cls, *parts):
        if parts:
            path = os.path.join(*[str(p) for p in parts])
        else:
            path = ''
        return str.__new__(cls, path)

    def __truediv__(self, other):
        return Path(self, other)

    __div__ = __truediv__

    def joinpath(self, *other):
        return Path(self, *other)

    def open(self, mode='r', encoding=None):
        return open(str(self), mode, encoding=encoding)

    def read_text(self, encoding='utf-8'):
        with open(str(self), 'r', encoding=encoding) as f:
            return f.read()

    def write_text(self, data, encoding='utf-8'):
        with open(str(self), 'w', encoding=encoding) as f:
            f.write(data)

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        path = str(self)
        if parents:
            try:
                os.makedirs(path, mode)
            except OSError:
                if not exist_ok and not os.path.isdir(path):
                    raise
        else:
            try:
                os.mkdir(path, mode)
            except OSError:
                if not exist_ok:
                    raise

    def resolve(self):
        return Path(os.path.abspath(str(self)))

    @property
    def parents(self):
        paths = []
        p = os.path.abspath(str(self))
        while True:
            p = os.path.dirname(p)
            paths.append(Path(p))
            if os.path.dirname(p) == p:
                break
        return _Parents(paths)

    def __fspath__(self):
        return str(self)

class _Parents(object):
    def __init__(self, items):
        self._items = items

    def __getitem__(self, idx):
        return self._items[idx]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)
