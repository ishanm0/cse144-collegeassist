import io
from threading import Thread
import os
import json

from src.config import DATA_DIR_PATH
from src.File.FileManager import create_unique_filename
from src.Logging.Logging import logger
from src.Web.GoogleCloudStorage import upload_file
from src.Web.WebCrawler import (
    ContentExtractor,
    LinkResolver,
    SessionManager,
    WebCrawler,
)

def upload_to_cloud(item):
    filename = item["url"].replace("https://", "").replace("http://", "").replace("/", "-")+".json"
    filename = os.path.join(DATA_DIR_PATH, filename)
    upload_file(io.BytesIO(json.dumps(item, indent=4).encode("utf-8")), filename)
    logger.info(f"Content from {item['url']} saved to {filename}")

if __name__ == "__main__":
    start_url = "https://admissions.ucsc.edu/"
    base_url = "ucsc.edu"

    max_depth = 10

    crawler = WebCrawler(SessionManager, LinkResolver, ContentExtractor)
    crawled_data = crawler.crawl(start_url, base_url, max_depth)
    num_crawled = 0

    for item in crawled_data:
        thread = Thread(target=upload_to_cloud, args=(item,))
        thread.start()
        num_crawled += 1
    
    logger.info(f"Total pages crawled: {num_crawled}")
    logger.info("All crawled data has been saved to individual files.")
