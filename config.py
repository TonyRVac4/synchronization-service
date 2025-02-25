import os
import sys

from dotenv import load_dotenv
from cloud_services import ChecksService

load_dotenv()


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Environment variable '{var_name}' wasn't found!")
    return value


try:
    LOCAL_DIR_PATH = get_env_variable("LOCAL_DIR_PATH")
    try:
        ChecksService.check_dir(LOCAL_DIR_PATH)
    except NotADirectoryError as not_dir_err:
        raise EnvironmentError(f"Env variable: {'LOCAL_DIR_PATH'} {not_dir_err}")
    except FileNotFoundError as not_found_err:
        raise EnvironmentError(f"Env variable: {'LOCAL_DIR_PATH'} {not_found_err}")

    CLOUD_TOKEN = get_env_variable("CLOUD_TOKEN")
    if not ChecksService.check_token(CLOUD_TOKEN, url="https://cloud-api.yandex.net/v1/disk/resources"):
        raise EnvironmentError(f"Env variable: {'CLOUD_TOKEN'} is invalid! Check your API key.")

    CLOUD_DIR_NAME = get_env_variable("CLOUD_DIR_NAME")
    SYNC_PERIOD = get_env_variable("SYNC_PERIOD")
    LOG_FILE_PATH = get_env_variable("LOG_FILE_PATH")
except FileNotFoundError as err:
    print(err, file=sys.stderr)
    exit(1)
except EnvironmentError as err:
    print(err, file=sys.stderr)
    exit(1)
