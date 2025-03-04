import os
import sys
import time
from multiprocessing.pool import ThreadPool, AsyncResult

from requests.exceptions import ConnectionError

from config import settings, print_to_stderr
from cloud_services import YandexCloudService
from ulits import logger_decorator, apply_decorator_for_all_methods
from logger_config import logger


def get_filenames_and_edit_time(dir_path: str) -> dict:
    local_files = {}

    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)

        if os.path.isfile(file_path) and not filename.startswith("."):
            local_files[filename] = round(os.path.getmtime(file_path), 2)

    return local_files


def synchronizer(service: YandexCloudService, local_dir_path: str) -> None:
    cloud_data: dict = service.get_info()
    local_data: dict = get_filenames_and_edit_time(local_dir_path)

    local_filenames: set = set(local_data.keys())
    cloud_filenames: set = set(cloud_data.keys())

    paths_to_upload: list[str] = [
        os.path.join(local_dir_path, filename)
        for filename in local_filenames - cloud_filenames
    ]
    paths_to_reload: list[str] = [
        os.path.join(local_dir_path, filename)
        for filename in local_filenames & cloud_filenames
        if cloud_data[filename] < local_data[filename]
    ]
    filenames_to_delete: list[str] = list(cloud_filenames - local_filenames)

    if paths_to_upload + paths_to_reload + filenames_to_delete:
        start = time.time()
        with ThreadPool(10) as pool:
            logger.info("Синхронизация началась.")

            results: list[AsyncResult] = []

            if paths_to_upload:
                results.append(pool.map_async(service.load, paths_to_upload))
            if paths_to_reload:
                results.append(pool.map_async(service.reload, paths_to_reload))
            if filenames_to_delete:
                results.append(pool.map_async(service.delete, filenames_to_delete))

            for res in results:
                res.get()

        elapsed_time = round(time.time() - start, 4)
        logger.info(f"Синхронизация завершена. Время выполнения: {elapsed_time} секунд.")


def main() -> None:
    apply_decorator_for_all_methods(logger_decorator(logger))(YandexCloudService)
    yandex_service = YandexCloudService(settings["CLOUD_TOKEN"], settings["CLOUD_DIR_NAME"])

    logger.info(f"Программа синхронизации файлов начинает работу с директорией '{settings['LOCAL_DIR_PATH']}'")
    print(f"Программа синхронизации файлов начинает работу с директорией '{settings['LOCAL_DIR_PATH']}'")
    try:
        while True:
            synchronizer(yandex_service, settings["LOCAL_DIR_PATH"])
            time.sleep(settings["SYNC_PERIOD"])
    except ConnectionError:
        logger.error("Программа синхронизации завершена. Проверте подключение к интернету.")
        print_to_stderr("Программа синхронизации завершена. Проверте подключение к интернету.")
    except KeyboardInterrupt:
        logger.info("Программа синхронизации завершена.")
        print("Программа синхронизации завершена.")
        sys.exit(0)
    except Exception as exp:
        logger.error(f"Программа синхронизации завершена из за ошибки: {exp}")
        print_to_stderr("Программа синхронизации завершена из за непредвиденной ошибки. Проверте логи.")


if __name__ == "__main__":
    main()
