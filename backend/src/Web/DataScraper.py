import os
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from src.Logging.Logging import logger
from src.Web.SSLAdapter import SSLAdapter

PARENT_DIR = os.path.dirname(os.getcwd())
OUTPUT_DIR = os.path.join(PARENT_DIR, "output")


class DataScraper:
    def __init__(
        self,
        id_column: str = "Slug",
        target_id: int = 283,
    ):
        self.id_column = id_column
        self.target_id = target_id
        self.session = requests.Session()
        self.session.mount("https://", SSLAdapter())
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def clean_text(self, text: str) -> str:
        cleaned_text = re.sub(r"[^\x20-\x7E\u0080-\uFFFF]", "", text)
        return cleaned_text

    def scrape_and_fill_text(self, url: str) -> str:
        if pd.isna(url):
            logger.info("Skipping empty URL.")
            return ""

        try:
            logger.info(f"Processing URL {url}...")
            headers = self.header
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            content = soup.find("div", class_="content")
            if content:
                paragraphs = content.find_all("p")
                text = "\n".join(p.get_text(strip=True) for p in paragraphs)
            else:
                text = "No content found."

            return self.clean_text(text)
        except Exception as e:
            logger.info(f"Error accessing URL {url}: {str(e)}")
            return ""

    def update_empty_text(self):
        df_empty_text = self.df[self.df["Text"].isna() & (self.df.index >= self.start_row)]

        for index, row in df_empty_text.iterrows():
            scraped_text = self.scrape_and_fill_text(row["URL"])
            self.df.at[index, "Text"] = scraped_text

        self.df.to_excel(self.excel_file_path, index=False)
        logger.info("Rescraping process and overwriting to Excel completed")

    def google_scrape_articles(self, search_keyword: str, top_article_index: int = 3, sleep_time: int = 3):
        # time.sleep(sleep_time)

        articles_list = []
        headers = self.header
        url = f"https://google.com/search?q={search_keyword}"

        logger.info(f"Sending request to {url}...")
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            logger.info("Request successful. Parsing articles...")
            soup = BeautifulSoup(response.content, "html.parser")
            search_results = soup.find_all("div", class_="tF2Cxc")

            if search_results:
                logger.info("Articles found:")
                for result in search_results:
                    title = result.find("h3").get_text()
                    link = result.find("a")["href"]
                    articles_list.append({"title": title, "link": link})
            else:
                logger.info("No articles found on the page.")
        else:
            logger.info(f"Failed to retrieve articles. Status code: {response.status_code}")

        return articles_list[:top_article_index]

    def scrape_article_content(self, article_link: str):
        logger.info(f"Request sent: {article_link}...")

        try:
            response = requests.get(article_link, headers=self.header, verify=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                paragraphs = soup.find_all("p")
                article_content = "\n".join(p.get_text() for p in paragraphs)
                return article_content
            else:
                logger.info("Failed to retrieve article content. " f"Status code: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.info(f"Error retrieving {article_link}: {str(e)}")
            return None

    def process_search(self, search_keyword: str, top_article_index: int = 1):
        max_retries = 1
        articles_list = self.google_scrape_articles(search_keyword, top_article_index=top_article_index)
        logger.info(search_keyword)
        logger.info(articles_list)
        result = []

        for item in articles_list:
            retries = 0
            content = None

            while content is None and retries < max_retries:
                content = self.scrape_article_content(item["link"])
                retries += 1
                if content is None:
                    logger.info(f"Retry {retries} for link: {item['link']}")

            if content is not None:
                result.append(content)
        return result
