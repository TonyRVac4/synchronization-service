import os
import sys
import time
from multiprocessing.pool import ThreadPool
from typing import Set, List

from requests.exceptions import ConnectionError

from config import CLOUD_DIR_NAME, CLOUD_TOKEN, SYNC_PERIOD, LOCAL_DIR_PATH, print_to_stderr
from cloud_services import YandexCloudService
from ulits import logger_decorator, apply_decorator_for_all_methods
from logger_config import logger


def synchronizer(service: YandexCloudService, sync_period: int = 60) -> None:
    while True:
        start = time.time()

        # Получаем имена файлов на облаке
        all_cloud_filenames: Set[str] = {
            file_info["name"]
            for file_info in service.get_info()
            if file_info["path"].startswith(f"disk:/{CLOUD_DIR_NAME}/")
        }
        # Получаем имена локальных файлов
        all_local_filenames: Set[str] = {
            filename
            for filename in os.listdir(LOCAL_DIR_PATH)
            if os.path.isfile(os.path.join(LOCAL_DIR_PATH, filename)) and not filename.startswith(".")
        }
        # Определяем, какие файлы нужно загрузить и удалить
        filenames_to_upload: Set[str] = all_local_filenames - all_cloud_filenames
        filenames_to_delete: List[str] = list(all_cloud_filenames - all_local_filenames)

        paths_to_upload: List[str] = [
            os.path.join(LOCAL_DIR_PATH, filename) for filename in filenames_to_upload
        ]

        if paths_to_upload + filenames_to_delete:
            with ThreadPool(10) as pool:
                logger.info("Синхронизация началась.")
                upload_result = pool.map_async(service.load, paths_to_upload)
                delete_result = pool.map_async(service.delete, filenames_to_delete)
                upload_result.get()
                delete_result.get()

            elapsed_time = round(time.time() - start, 4)
            logger.info(f"Синхронизация завершена. Время выполнения: {elapsed_time} секунд.")
        time.sleep(sync_period)


if __name__ == "__main__":
    #подключает логер для необходимых методов
    apply_decorator_for_all_methods(logger_decorator(logger))(YandexCloudService)

    service = YandexCloudService(CLOUD_TOKEN, CLOUD_DIR_NAME)

    greet_msg = f"Программа синхронизации файлов начинает работу с директорией '{LOCAL_DIR_PATH}'"
    bye_msg = "Программа синхронизации завершена."
    connection_err_msg = "Программа синхронизации завершена. Проверте подключение к интернету."

    logger.info(greet_msg)
    print(greet_msg)

    try:
        synchronizer(service, SYNC_PERIOD)
    except ConnectionError as err:
        logger.error(connection_err_msg)
        print_to_stderr(connection_err_msg)
    except KeyboardInterrupt:
        logger.info(bye_msg)
        print(bye_msg)
        sys.exit(0)
    except Exception as exp:
        logger.error(f"Программа синхронизации завершена из за ошибки: {exp}")
        print_to_stderr("Программа синхронизации завершена из за непредвиденной ошибки. Проверте логи.")
