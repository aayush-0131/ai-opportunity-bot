"""
LinkedIn Jobs Crawler
"""
from typing import Dict, List
from bs4 import BeautifulSoup
from urllib.parse import quote
from .base_crawler import BaseCrawler
import logging

logger = logging.getLogger(__name__)


class LinkedInCrawler(BaseCrawler):
    """
    Crawler for LinkedIn Jobs.
    Note: LinkedIn heavily rate-limits scraping. Consider using their official API.
    """
    
    def __init__(self):
        super().__init__(
            source_name="LinkedIn",
            base_url="https://www.linkedin.com/jobs",
            delay=3.0  # Higher delay for LinkedIn
        )
    
    def build_search_url(self, query: str, page: int) -> str:
        """Build LinkedIn job search URL"""
        start = (page - 1) * 25  # LinkedIn shows 25 jobs per page
        encoded_query = quote(query)
        return f"{self.base_url}/search/?keywords={encoded_query}&start={start}"
    
    def parse_listing_page(self, html: str) -> List[str]:
        """
        Extract job URLs from LinkedIn search results.
        
        Returns:
            List of job URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        job_urls = []
        
        try:
            # LinkedIn job cards have specific class names (these may change!)
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards:
                link = card.find('a', class_='base-card__full-link')
                if link and link.get('href'):
                    job_url = link['href'].split('?')[0]  # Remove tracking params
                    job_urls.append(job_url)
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn listing page: {str(e)}")
        
        return job_urls
    
    def parse_opportunity_page(self, html: str, url: str) -> Dict:
        """
        Extract job details from LinkedIn job page.
        
        Returns:
            Dictionary with job details
        """
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            opportunity = {
                'url': url,
                'title': None,
                'company': None,
                'location': None,
                'description': None,
                'job_type': None,
                'posted_date': None,
            }
            
            # Extract title
            title_elem = soup.find('h1', class_='top-card-layout__title')
            if title_elem:
                opportunity['title'] = title_elem.text.strip()
            
            # Extract company
            company_elem = soup.find('a', class_='topcard__org-name-link')
            if company_elem:
                opportunity['company'] = company_elem.text.strip()
            
            # Extract location
            location_elem = soup.find('span', class_='topcard__flavor--bullet')
            if location_elem:
                opportunity['location'] = location_elem.text.strip()
            
            # Extract description
            desc_elem = soup.find('div', class_='show-more-less-html__markup')
            if desc_elem:
                opportunity['description'] = desc_elem.get_text(separator=' ', strip=True)
            
            # Extract job type
            criteria = soup.find_all('li', class_='description__job-criteria-item')
            for item in criteria:
                subheader = item.find('h3')
                if subheader and 'Employment type' in subheader.text:
                    value = item.find('span', class_='description__job-criteria-text')
                    if value:
                        opportunity['job_type'] = value.text.strip()
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job page {url}: {str(e)}")
            return None
