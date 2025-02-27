import os
import requests
from abc import ABC, abstractmethod
from typing import Any


class AbstractCloudService(ABC):
    @abstractmethod
    def load(self, path: str) -> dict[str, Any]:
        """Загрузка файла в хранилище."""
        pass

    @abstractmethod
    def reload(self, path: str) -> dict[str, Any]:
        """Перезапись файла в хранилище."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> dict[str, Any]:
        """Удаление файла из хранилища."""
        pass

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Получение информации о хранящихся в удалённом хранилище файлах."""
        pass


class CheckService:
    @staticmethod
    def check_token(token: str, url: str) -> bool:
        result = requests.get(url=url, headers={
            "Accept": "application/json",
            "Authorization": f"OAuth {token}",
        },
                              )
        if result.status_code == 401:
            return False
        return True


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
            201: {"status_code": 201, "message": "Файл загружен", "result": True},
            202: {"status_code": 202, "message": "Запрос принят сервером, но ещё не обработан", "result": True},
            204: {"status_code": 204, "message": "Файл успешно удален", "result": True},
            401: {"status_code": 401, "message": "Не авторизован. Проверте наличие и валидность API ключа", "result": False},
            404: {"status_code": 404, "message": "Файл не найден", "result": False},
            412: {"status_code": 412,
                  "message": "При дозагрузке файла был передан неверный диапазон в заголовке Content-Range",
                  "result": False},
            413: {"status_code": 413, "message": "Размер файла больше допустимого", "result": False},
            500: {"status_code": 500, "message": "Ошибка сервера, попробуйте повторить загрузку", "result": False},
            503: {"status_code": 503, "message": "Ошибка сервера, попробуйте повторить загрузку", "result": False},
            517: {"status_code": 517, "message": "Для загрузки файла не хватает места на Диске пользователя",
                  "result": False},
        }

    @staticmethod
    def __check_file(path) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"No such file or directory: '{path}'")
        elif os.path.isdir(path):
            raise IsADirectoryError(f"Must be a path to file: '{path}'")

    def __get_response_message(self, code) -> dict[str, Any]:
        try:
            response = self.__status_codes[code]
        except KeyError:
            response = {"status_code": code, "message": "Произошло нечто непредвиденное.", "result": False}
        return response

    def __get_target_url(self, remote_path, overwrite: bool = False) -> dict[str, Any]:
        request = requests.get(
            url=f"{self.__base_url}/upload?path={remote_path}&overwrite={str(overwrite).lower()}",
            headers=self.__headers,
        )
        response_data: dict = request.json()

        if "error" in response_data:
            return {"status_code": request.status_code, "message": response_data["message"], "result": False}
        return {"url": response_data["href"], "result": True}

    def __upload_file(self, path: str, overwrite: bool = False) -> dict[str, Any]:
        self.__check_file(path)

        filename = path.split('/')[-1]

        cloud_dir_file_path = f"{self.__remote_dir_name}/{filename}"

        target_url = self.__get_target_url(cloud_dir_file_path, overwrite)
        if not target_url["result"]:
            return target_url

        with open(path, "rb") as file:
            request = requests.put(target_url["url"], headers=self.__headers, data=file)

        result = self.__get_response_message(request.status_code)

        if overwrite:
            result["message"] = f"Файл '{filename}' успешно перезаписан."
        result["message"] = f"Файл '{filename}' успешно записан."
        return result

    def load(self, path) -> dict[str, Any]:
        result = self.__upload_file(path)

        return result

    def reload(self, path) -> dict[str, Any]:
        result = self.__upload_file(path, overwrite=True)

        return result

    def delete(self, filename, from_trash: bool = False) -> dict[str, Any]:
        file_path = f"{self.__remote_dir_name}/{filename}"

        request = requests.delete(
            url=f"{self.__base_url}?path={file_path}&permanently={str(from_trash).lower()}",
            headers=self.__headers,
        )

        result: dict = self.__get_response_message(request.status_code)
        if request.status_code == 204:
            result["message"] = f"Файл '{filename}' успешно удален"
        return result

    def get_info(self) -> list[dict]:
        request = requests.get(
            url=f"{self.__base_url}/files",
            headers=self.__headers,
        )
        if request.status_code == 200:
            requested_data: list[dict] = request.json()["items"]
            required_data: list = []

            for file in requested_data:
                required_data.append(
                    {
                        "name": file["name"],
                        "path": file["path"],
                        "size": file["size"],
                        "media_type": file["media_type"],
                        "created": file["created"],
                        "modified": file["modified"],
                    }
                )
            return required_data
        else:
            return self.__get_response_message(request.status_code)
