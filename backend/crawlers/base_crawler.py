import time
import requests
from abc import ABC, abstractmethod


class BaseCrawler(ABC):
    def __init__(self, rate_limit=1):
        self.rate_limit = rate_limit

    def crawl(self, url):
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an error for bad responses
                time.sleep(self.rate_limit)  # Respect rate limiting
                return response.text
            except requests.RequestException as e:
                print(f"Error occurred: {e}")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    @abstractmethod
    def parse_listing_page(self, html):
        pass

    @abstractmethod
    def parse_opportunity_page(self, html):
        pass
