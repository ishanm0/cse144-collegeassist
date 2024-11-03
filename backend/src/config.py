import datetime
import os

FolderYear = datetime.datetime.now().strftime("%Y")
FolderDate = datetime.datetime.now().strftime("%m-%d")
LogFileName = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

LOG_FILE_PATH = f".log/{FolderYear}/{FolderDate}/{LogFileName}"
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

DataFileName = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.data"
DATA_FILE_PATH = f".data/{FolderYear}/{FolderDate}/{DataFileName}"
DATA_DIR_PATH = f"/{FolderDate}"
os.makedirs(os.path.dirname(DATA_DIR_PATH), exist_ok=True)
