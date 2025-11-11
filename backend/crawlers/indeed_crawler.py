"""
Indeed Jobs Crawler
"""
from typing import Dict, List
from bs4 import BeautifulSoup
from urllib.parse import quote
from .base_crawler import BaseCrawler
import logging

logger = logging.getLogger(__name__)


class IndeedCrawler(BaseCrawler):
    """Crawler for Indeed job listings"""
    
    def __init__(self):
        super().__init__(
            source_name="Indeed",
            base_url="https://www.indeed.com",
            delay=2.0
        )
    
    def build_search_url(self, query: str, page: int) -> str:
        """Build Indeed job search URL"""
        start = (page - 1) * 10
        encoded_query = quote(query)
        return f"{self.base_url}/jobs?q={encoded_query}&start={start}"
    
    def parse_listing_page(self, html: str) -> List[str]:
        """Extract job URLs from Indeed search results"""
        soup = BeautifulSoup(html, 'lxml')
        job_urls = []
        
        try:
            # Indeed uses mosaic-provider-jobcards
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards:
                link = card.find('a', class_='jcs-JobTitle')
                if link and link.get('href'):
                    job_url = self.base_url + link['href']
                    job_urls.append(job_url)
            
        except Exception as e:
            logger.error(f"Error parsing Indeed listing page: {str(e)}")
        
        return job_urls
    
    def parse_opportunity_page(self, html: str, url: str) -> Dict:
        """Extract job details from Indeed job page"""
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            opportunity = {
                'url': url,
                'title': None,
                'company': None,
                'location': None,
                'description': None,
                'salary': None,
                'job_type': None,
            }
            
            # Extract title
            title_elem = soup.find('h1', class_='jobsearch-JobInfoHeader-title')
            if title_elem:
                opportunity['title'] = title_elem.text.strip()
            
            # Extract company
            company_elem = soup.find('div', {'data-company-name': True})
            if company_elem:
                opportunity['company'] = company_elem.get('data-company-name')
            
            # Extract location
            location_elem = soup.find('div', {'data-testid': 'job-location'})
            if location_elem:
                opportunity['location'] = location_elem.text.strip()
            
            # Extract salary
            salary_elem = soup.find('div', {'id': 'salaryInfoAndJobType'})
            if salary_elem:
                opportunity['salary'] = salary_elem.text.strip()
            
            # Extract description
            desc_elem = soup.find('div', {'id': 'jobDescriptionText'})
            if desc_elem:
                opportunity['description'] = desc_elem.get_text(separator=' ', strip=True)
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error parsing Indeed job page {url}: {str(e)}")
            return None
