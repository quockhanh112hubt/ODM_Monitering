import os

CURRENT_VERSION_FILE = "C:\\ODM_Monitering\\version.txt"

def get_current_version():
    if os.path.exists(CURRENT_VERSION_FILE):
        with open(CURRENT_VERSION_FILE, "r") as file:
            return file.read().strip()
    return "0.0.0"