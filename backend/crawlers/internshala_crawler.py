"""
Internshala Internships Crawler
"""
from typing import Dict, List
from bs4 import BeautifulSoup
from urllib.parse import quote
from .base_crawler import BaseCrawler
import logging

logger = logging.getLogger(__name__)


class InternShalaCrawler(BaseCrawler):
    """Crawler for Internshala internship listings"""
    
    def __init__(self):
        super().__init__(
            source_name="Internshala",
            base_url="https://internshala.com",
            delay=2.0
        )
    
    def build_search_url(self, query: str, page: int) -> str:
        """Build Internshala search URL"""
        encoded_query = quote(query)
        return f"{self.base_url}/internships/keywords-{encoded_query}/page-{page}"
    
    def parse_listing_page(self, html: str) -> List[str]:
        """Extract internship URLs from Internshala search results"""
        soup = BeautifulSoup(html, 'lxml')
        internship_urls = []
        
        try:
            # Internshala internship cards
            containers = soup.find_all('div', class_='internship_meta')
            
            for container in containers:
                link = container.find('a', href=True)
                if link:
                    internship_url = self.base_url + link['href']
                    internship_urls.append(internship_url)
            
        except Exception as e:
            logger.error(f"Error parsing Internshala listing page: {str(e)}")
        
        return internship_urls
    
    def parse_opportunity_page(self, html: str, url: str) -> Dict:
        """Extract internship details from Internshala page"""
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            opportunity = {
                'url': url,
                'title': None,
                'company': None,
                'location': None,
                'description': None,
                'duration': None,
                'stipend': None,
                'type': 'internship',
            }
            
            # Extract title
            title_elem = soup.find('span', class_='profile_on_detail_page')
            if title_elem:
                opportunity['title'] = title_elem.text.strip()
            
            # Extract company
            company_elem = soup.find('div', class_='company_name')
            if company_elem:
                opportunity['company'] = company_elem.text.strip()
            
            # Extract location
            location_elem = soup.find('div', class_='location_link')
            if location_elem:
                opportunity['location'] = location_elem.text.strip()
            
            # Extract duration
            duration_elem = soup.find('div', class_='item_body', string=lambda t: t and 'Duration' in t)
            if duration_elem:
                opportunity['duration'] = duration_elem.text.strip()
            
            # Extract stipend
            stipend_elem = soup.find('span', class_='stipend')
            if stipend_elem:
                opportunity['stipend'] = stipend_elem.text.strip()
            
            # Extract description
            desc_elem = soup.find('div', class_='internship_details')
            if desc_elem:
                opportunity['description'] = desc_elem.get_text(separator=' ', strip=True)
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error parsing Internshala page {url}: {str(e)}")
            return None
