# my_importer.py
import imp
import sys
import importlib
import types
import datetime


class UrlMetaFinder(importlib.abc.MetaPathFinder):
    def __init__(self, code_file_data):
        self.code_file_data = code_file_data
        self.file_name = None

    def find_module(self, fullname, path=None):
        try:
            loader = UrlMetaLoader(self.code_file_data)
            self.file_name = fullname
            # print(self.file_name)
            # print(loader.file_name)
            loader.load_module(fullname)
            return loader
        except Exception:
            return None


class UrlMetaLoader(importlib.abc.SourceLoader):
    def __init__(self, code_file_data):
        self.code_file_data = code_file_data

    def get_code(self, fullname):
        return self.code_file_data

    def load_module(self, fullname):
        code = self.get_code(fullname)
        # print(fullname)
        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
        mod.__file__ = self.get_filename(fullname)
        mod.__loader__ = self
        mod.__package__ = fullname
        exec(code, mod.__dict__)
        return None

    def get_data(self):
        pass

    def get_filename(self, fullname):
        return fullname + '.py'


def install_meta(code_file_data):
    finder = UrlMetaFinder(code_file_data)
    sys.meta_path.append(finder)
    name = f'py{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    _temp = importlib.reload(importlib.import_module(name))
    sys.meta_path.remove(finder)
    return {name: item for name, item in vars(_temp).items() if isinstance(item, types.FunctionType)}

