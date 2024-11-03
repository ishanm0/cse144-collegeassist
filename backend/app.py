import io

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

if __name__ == "__main__":
    start_url = "https://admissions.ucsc.edu/"
    max_depth = 10

    crawler = WebCrawler(SessionManager, LinkResolver, ContentExtractor)
    crawled_data = crawler.crawl(start_url, max_depth)

    for item in crawled_data:
        filename = create_unique_filename(item["url"], DATA_DIR_PATH)
        upload_file(io.BytesIO(item["text"].encode("utf-8")), filename)
        logger.info(f"Content from {item['url']} saved to {filename}")

    logger.info(f"Total pages crawled: {len(crawled_data)}")
    logger.info("All crawled data has been saved to individual files.")
