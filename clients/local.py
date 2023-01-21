import os
import shutil
import json
import logging


class NoCachedData(Exception):
    pass


class LocalCacheClient:
    """ Local Cache Client class """

    def __init__(self, dir_path):
        self.dir_path = dir_path
        if not os.path.exists(self.dir_path):
            logging.info(f"creating cache directory {self.dir_path}")
            os.makedirs(self.dir_path)

    def save(self, data, file_path, file_name=None):
        file_name = file_name if file_name else "data.json"
        _path = os.path.join(self.dir_path, file_path)
        if not os.path.exists(_path):
            os.makedirs(_path)
            logging.info(f"storing new {file_name} under {_path}")
            with open(f"{_path}/{file_name}", "w") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        else:
            logging.info(f"updating {file_name} under {_path}")
            with open(f"{_path}/{file_name}", "r+") as file:
                file_data = json.load(file)
                file.seek(0)
                data = {**file_data, **data}
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.truncate()

    def load(self, file_path, file_name=None):
        file_name = file_name if file_name else "data.json"
        _path = os.path.join(self.dir_path, file_path)
        if not os.path.exists(_path):
            raise NoCachedData
        else:
            logging.info(f"loading {file_name} from {_path}")
            with open(f"{_path}/{file_name}", "r") as file:
                data = json.load(file)
                return data

    def delete(self, dir_path):
        _path = os.path.join(self.dir_path, dir_path)
        shutil.rmtree(_path, onerror=FileNotFoundError)
        logging.info(f"path {_path} was removed")
        for current_dir, sub_dirs, files in os.walk(self.dir_path, topdown=False):
            for _dir in sub_dirs:
                dir_path = os.path.join(current_dir, _dir)
                if not os.listdir(dir_path):
                    logging.info(f"cleaned up {dir_path}")
                    os.rmdir(os.path.realpath(os.path.join(dir_path)))
