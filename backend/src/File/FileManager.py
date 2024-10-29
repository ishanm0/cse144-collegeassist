import hashlib
import os


def create_unique_filename(url, data_dir_path):
    """Generates a unique filename based on the URL."""
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    filename = f"{url_hash}.txt"
    return os.path.join(data_dir_path, filename)
