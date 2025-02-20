import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Environment variable '{var_name}' wasn't found!")
    return value


def check_if_path_exist(path: str) -> str:
    check = os.path.exists(path)
    if not check:
        raise FileNotFoundError(f"Directory '{path}' wasn't found!")
    return path


try:
    LOCAL_DIR_PATH = check_if_path_exist(get_env_variable("LOCAL_DIR_PATH"))
    CLOUD_DIR_NAME = get_env_variable("CLOUD_DIR_NAME")
    CLOUD_TOKEN = get_env_variable("CLOUD_TOKEN")
    SYNC_PERIOD = get_env_variable("SYNC_PERIOD")
    LOG_FILE_PATH = get_env_variable("LOG_FILE_PATH")
except FileNotFoundError as err:
    print(err, file=sys.stderr)
    exit(1)
except EnvironmentError as err:
    print(err, file=sys.stderr)
    exit(1)
