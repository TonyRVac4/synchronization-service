import os
import time
from multiprocessing.pool import ThreadPool
from typing import Set, List

from config import CLOUD_DIR_NAME, CLOUD_TOKEN, SYNC_PERIOD, LOCAL_DIR_PATH
from cloud_services import YandexCloudService


def main_loop(service: YandexCloudService) -> None:
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
            if os.path.isfile(os.path.join(LOCAL_DIR_PATH, filename))
        }

        # Определяем, какие файлы нужно загрузить и удалить
        filenames_to_upload: Set[str] = all_local_filenames - all_cloud_filenames
        filenames_to_delete: List[str] = list(all_cloud_filenames - all_local_filenames)

        paths_to_upload: List[str] = [
            os.path.join(LOCAL_DIR_PATH, filename) for filename in filenames_to_upload
        ]

        if paths_to_upload + filenames_to_delete:
            with ThreadPool(10) as pool:
                upload_result = pool.map_async(service.load, paths_to_upload)
                delete_result = pool.map_async(service.delete, filenames_to_delete)
                upload_outcome = upload_result.get()
                delete_outcome = delete_result.get()

            elapsed_time = round(time.time() - start, 4)
            print(f"Время выполнения: {elapsed_time} секунд")
            print("Результаты загрузки:", upload_outcome)
            print("Результаты удаления:", delete_outcome)

        time.sleep(int(SYNC_PERIOD))


if __name__ == "__main__":
    service = YandexCloudService(CLOUD_TOKEN, CLOUD_DIR_NAME)
    main_loop(service)
