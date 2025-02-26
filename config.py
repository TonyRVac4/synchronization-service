import os
import sys

from dotenv import load_dotenv
from cloud_services import ChecksService

load_dotenv()


def print_to_stderr(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print_to_stderr(f"Env variable '{var_name}' wasn't found!")
    return value


LOCAL_DIR_PATH = get_env_variable("LOCAL_DIR_PATH")
if not os.path.exists(LOCAL_DIR_PATH):
    print_to_stderr(f"Env variable 'LOCAL_DIR_PATH' is invalid.\nNo such directory: '{LOCAL_DIR_PATH}'")
elif not os.path.isdir(LOCAL_DIR_PATH):
    print_to_stderr(f"Env variable 'LOCAL_DIR_PATH' is invalid.\nMust be a path to directory: '{LOCAL_DIR_PATH}'.")

CLOUD_TOKEN = get_env_variable("CLOUD_TOKEN")
if not ChecksService.check_token(CLOUD_TOKEN, url="https://cloud-api.yandex.net/v1/disk/resources"):
    print_to_stderr(f"Env variable: 'CLOUD_TOKEN' is invalid! Check your API key.")

SYNC_PERIOD = get_env_variable("SYNC_PERIOD")
if not SYNC_PERIOD.isdigit() or int(SYNC_PERIOD) <= 0:
    print_to_stderr(f"Env variable 'SYNC_PERIOD' variable must be int and greater than 0!")

LOG_FILE_PATH = get_env_variable("LOG_FILE_PATH")
if os.path.isdir(LOG_FILE_PATH) or not LOG_FILE_PATH.endswith(".log"):
    print_to_stderr("Env variable 'LOG_FILE_PATH' must be a file with '.log' extension.")

CLOUD_DIR_NAME = get_env_variable("CLOUD_DIR_NAME")
