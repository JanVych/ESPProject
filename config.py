import json

import os


class Config:
    def __init__(self, file_path: str):
        self.file_path = file_path
        try:
            with open(self.file_path, "r") as file:
                config_string = file.read()
        except OSError:
            print(f"cant open file: {self.file_path}")
        try:
            self.config = json.loads(config_string)
        except ValueError:
            config_string = "{}"
            self.config = json.loads(config_string)
        self.__save_file(config_string)

    def __save_file(self, json_string: str) -> None:
        try:
            with open(self.file_path, "w") as file:
                file.write(json_string)
        except OSError:
            print(f"cant open file: {self.file_path}")

    def __delete_file(self) -> None:
        try:
            os.remove(self.file_path)
        except Exception as exp:
            print(f"error: {exp}, file:{self.file_path} ")

    def clear_config(self) -> None:
        self.__save_file("{}")
        self.config = json.loads("{}")

    def set(self, key: str, value: object) -> None:
        self.config[key] = value
        self.__save_file(json.dumps(self.config))

    def get(self, key: str) -> object:
        if self.config:
            return self.config[key]
