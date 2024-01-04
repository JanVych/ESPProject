import json


class Config:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        try:
            with open(self.file_path, "r") as file:
                config = file.read()
        except OSError:
            print(f"cant open file: {self.file_path}")

        try:
            self.config = json.loads(config)
        except ValueError:
            config = "{}"
            self.config = json.loads(config)
        self.__save_file(config)

    def __save_file(self, json_string: str):
        try:
            with open(self.file_path, "w") as file:
                file.write(json_string)
        except OSError:
            print(f"cant open file: {self.file_path}")

    def set(self, key: str, value: object) -> None:
        self.config[key] = value
        self.__save_file(json.dumps(self.config))

    def get(self, key: str) -> object:
        if self.config:
            return self.config[key]
