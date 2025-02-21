import os

import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class AbstractCloudService(ABC):
    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """Загрузка файла в хранилище."""
        pass

    @abstractmethod
    def reload(self, path: str) -> Dict[str, Any]:
        """Перезапись файла в хранилище."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> Dict[str, Any]:
        """Удаление файла из хранилища."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Получение информации о хранящихся в удалённом хранилище файлах."""
        pass


class YandexCloudService(AbstractCloudService):
    def __init__(self, token: str, remote_dir_name: str) -> None:
        self.__access_token = token
        self.__remote_dir_name = remote_dir_name
        self.__base_url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.__headers = {
            "Accept": "application/json",
            "Authorization": f"OAuth {self.__access_token}"
        }
        self.__status_codes = {
            201: {"status_code": 201, "message": "Файл загружен.", "result": True},
            202: {"status_code": 202, "message": "Файл успешно удален.", "result": True},
            204: {"status_code": 204, "message": "Запрос принят сервером, но ещё не обработан.", "result": True},
            404: {"status_code": 204, "message": "Файл не найден.", "result": False},
            412: {"status_code": 412,
                  "message": "При дозагрузке файла был передан неверный диапазон в заголовке Content-Range.",
                  "result": False},
            413: {"status_code": 413, "message": "Размер файла больше допустимого.", "result": False},
            500: {"status_code": 500, "message": "Ошибка сервера, попробуйте повторить загрузку.", "result": False},
            503: {"status_code": 500, "message": "Ошибка сервера, попробуйте повторить загрузку.", "result": False},
            517: {"status_code": 517, "message": "Для загрузки файла не хватает места на Диске пользователя.",
                  "result": False},
        }

    @staticmethod
    def __check_file(path) -> None:
        if not os.path.exists(path) or os.path.isdir(path):
            raise FileNotFoundError(f"No such file or directory: '{path}'")

    def __get_response_message(self, code) -> Dict[str, Any]:
        try:
            response = self.__status_codes[code]
        except KeyError:
            response = {"status_code": code, "message": "Произошло нечто непредвиденное.", "result": False}
        return response

    def __get_target_url(self, path, overwrite: bool = False) -> Dict[str, Any]:
        file_path = f"{self.__remote_dir_name}/{path.split('/')[-1]}"

        request = requests.get(
            url=f"{self.__base_url}/upload?path={file_path}&overwrite={str(overwrite).lower()}",
            headers=self.__headers,
        )
        response_data: dict = request.json()

        if "error" in response_data:
            match response_data["error"]:
                case "DiskPathDoesntExistsError":
                    return {"status_code": 404, "message": f"Указанного пути '{file_path}' не существует.",
                            "result": False}
                case "DiskResourceAlreadyExistsError":
                    return {"status_code": 409, "message": f"Ресурс '{file_path}' уже существует.", "result": False}

        return {"url": response_data["href"], "result": True}

    def __upload_file(self, path: str, overwrite: bool = False) -> Dict[str, Any]:
        self.__check_file(path)

        target_url = self.__get_target_url(path, overwrite)
        if not target_url["result"]:
            return target_url

        with open(path, "rb") as file:
            response = requests.put(target_url["url"], headers=self.__headers, data=file)
        return self.__get_response_message(response.status_code)

    def load(self, path) -> Dict[str, Any]:
        return self.__upload_file(path)

    def reload(self, path) -> Dict[str, Any]:
        return self.__upload_file(path, overwrite=True)

    def delete(self, filename) -> Dict[str, Any]:
        file_path = f"{self.__remote_dir_name}/{filename}"
        try:
            request = requests.delete(
                url=f"{self.__base_url}?path={file_path}&permanently=false",
                headers=self.__headers,
            )
            return self.__get_response_message(request.status_code)
        except Exception as exp:
            #logging
            return {"status_code": 500, "message": exp}

    def get_info(self) -> Dict[str, Any]:
        try:
            request = requests.get(
                url=f"{self.__base_url}/files",
                headers=self.__headers,
            )
            if request.status_code == 200:
                requested_data: List[dict] = request.json()["items"]
                required_data: dict = {}

                for index, file in enumerate(requested_data):
                    required_data[index + 1] = {
                            "name": file["name"],
                            "path": file["path"],
                            "size": file["size"],
                            "media_type": file["media_type"],
                            "created": file["created"],
                            "modified": file["modified"],
                        }
                return required_data
            # handle if not 200
        except Exception as exp:
            #logging
            return {"status_code": 500, "message": exp}
