import io
from threading import Thread
import os

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
    filename = item["url"].replace("https://", "").replace("http://", "").replace("/", "_")
    filename = os.path.join(DATA_DIR_PATH, filename)
    upload_file(io.BytesIO(item["text"].encode("utf-8")), filename)
    logger.info(f"Content from {item['url']} saved to {filename}")

if __name__ == "__main__":
    start_url = "https://admissions.ucsc.edu/"
    max_depth = 1

    crawler = WebCrawler(SessionManager, LinkResolver, ContentExtractor)
    crawled_data = crawler.crawl(start_url, max_depth)
    num_crawled = 0

    for item in crawled_data:
        # filename = create_unique_filename(item["url"], DATA_DIR_PATH)
        # filename = item["text"]
        # upload_file(io.BytesIO(item["text"].encode("utf-8")), filename)
        # logger.info(f"Content from {item['url']} saved to {filename}")
        thread = Thread(target=upload_to_cloud, args=(item,))
        thread.start()
        num_crawled += 1
    
    logger.info(f"Total pages crawled: {num_crawled}")
    logger.info("All crawled data has been saved to individual files.")
