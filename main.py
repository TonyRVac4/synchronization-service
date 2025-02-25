import os
import time
from multiprocessing.pool import ThreadPool
from typing import Set, List
from logger import logger
from config import CLOUD_DIR_NAME, CLOUD_TOKEN, SYNC_PERIOD, LOCAL_DIR_PATH
from cloud_services import YandexCloudService


def synchronizer(service: YandexCloudService) -> None:
    while True:
        start = time.time()

        # Получаем имена файлов на облаке
        all_cloud_filenames: Set[str] = {
            file_info["name"]
            for file_info in service.get_info().values()
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
            logger.info(f"Синхронизация окончена. Время выполнения: {elapsed_time} секунд.")
        time.sleep(int(SYNC_PERIOD))


if __name__ == "__main__":
    service = YandexCloudService(CLOUD_TOKEN, CLOUD_DIR_NAME, logger)

    logger.info(f"Программа синхронизации файлов начинает работу с директорией '{LOCAL_DIR_PATH}'")
    try:
        synchronizer(service)
    except KeyboardInterrupt:
        logger.info(f"Программа синхронизации завершена.")
