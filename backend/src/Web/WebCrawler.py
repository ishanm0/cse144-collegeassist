from collections import deque

import requests
from bs4 import BeautifulSoup
from src.Logging.Logging import logger
from src.Web.SSLAdapter import SSLAdapter
import markdownify
import re
import tldextract


class SessionManager:
    """Manages the creation of a session with specific headers and SSL configurations."""

    @staticmethod
    def create_session():
        session = requests.Session()
        session.mount("https://", SSLAdapter())
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            }
        )
        return session


class LinkResolver:
    """Handles URL resolution and filtering of links on a page."""

    @staticmethod
    def resolve_links(url, base_url, soup, visited):
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if not href.startswith("http"):
                href = requests.compat.urljoin(url, href)
            if href not in visited and LinkResolver.same_domain(href, base_url) and not "#" in href:
                links.append(href)
        return links
    
    @staticmethod
    def same_domain(url, base_url):
        sub_parts = tldextract.extract(url)
        parent_parts = tldextract.extract(base_url)

        # Compare the root domain and suffix
        return (sub_parts.domain == parent_parts.domain and
                sub_parts.suffix == parent_parts.suffix)


class ContentExtractor:
    """Extracts and cleans text content from a given HTML page."""

    @staticmethod
    def extract_all_text(soup):
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def extract_main_text(soup):
        main_content = soup.find("main")
        if main_content:
            return main_content.get_text(separator="\n", strip=True)
        else:
            return "No <main> content found."
        
    @staticmethod
    def convert_to_md(soup):
        html = soup.find("main") or soup.find("body") or soup
        text = markdownify.markdownify(str(html), strip=["a", "img"])
        text = re.sub(r"\n\n+", "\n", text).strip()

        return text

class WebCrawler:
    """Crawls a website up to a given depth and returns page content."""

    def __init__(self, session_manager: SessionManager, link_resolver: LinkResolver, content_extractor: ContentExtractor):
        self.session = session_manager.create_session()
        self.link_resolver = link_resolver
        self.content_extractor = content_extractor

    def crawl(self, start_url, base_url, max_depth):
        visited = set()
        queue = deque([(start_url, 0)])

        while queue:
            url, depth = queue.popleft()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            logger.info(f"Crawling URL at depth {depth}: {url}")

            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                text = self.content_extractor.convert_to_md(soup)
                data =  {"url": url, "title": soup.find('title').text, "depth": depth, "text": text}
                new_links = self.link_resolver.resolve_links(url, base_url, soup, visited)
                for link in new_links:
                    queue.append((link, depth + 1))
                
                yield data

            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
