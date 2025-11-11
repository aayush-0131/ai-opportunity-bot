"""
AI-Powered Opportunity Parser using GPT-4
Converts unstructured HTML/text into structured opportunity data
"""
import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpportunityParser:
    """
    Uses GPT-4 to extract and normalize opportunity data from raw HTML/text.
    Handles edge cases, incomplete data, and provides fallback parsing.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the parser with OpenAI API key.
        
        Args:
            api_key: OpenAI API key (defaults to env variable)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Cost-effective for parsing
        
    def clean_html(self, html: str, max_length: int = 8000) -> str:
        """
        Clean and truncate HTML to reduce token usage.
        
        Args:
            html: Raw HTML content
            max_length: Maximum character length
            
        Returns:
            Cleaned text
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}")
            return html[:max_length]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def parse_opportunity(self, raw_content: str, source_url: str) -> Optional[Dict]:
        """
        Parse opportunity details using GPT-4.
        
        Args:
            raw_content: Raw HTML or text content
            source_url: URL of the opportunity
            
        Returns:
            Structured opportunity dictionary or None if parsing fails
        """
        try:
            # Clean the content
            cleaned_content = self.clean_html(raw_content)
            
            # Build the prompt
            prompt = self._build_extraction_prompt(cleaned_content, source_url)
            
            # Call GPT-4
            logger.info(f"Parsing opportunity from: {source_url}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting job and internship information from web pages. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=1000
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and clean the result
            opportunity = self._validate_and_clean(result, source_url)
            
            if opportunity:
                logger.info(f"✅ Successfully parsed: {opportunity.get('title', 'Unknown')}")
                return opportunity
            else:
                logger.warning(f"⚠️ Validation failed for: {source_url}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {source_url}: {str(e)}")
            return self._fallback_parse(raw_content, source_url)
            
        except Exception as e:
            logger.error(f"Error parsing opportunity {source_url}: {str(e)}")
            return self._fallback_parse(raw_content, source_url)
    
    def _build_extraction_prompt(self, content: str, url: str) -> str:
        """Build the GPT-4 extraction prompt"""
        return f"""
Extract job/internship opportunity details from this webpage content.

URL: {url}

Content:
{content}

Extract and return ONLY a JSON object with these exact fields:
{{
    "title": "job/internship title",
    "company": "company or organization name",
    "type": "job|internship|scholarship|fellowship|grant",
    "location": "city, state/country or 'Remote'",
    "remote": true or false,
    "deadline": "YYYY-MM-DD or null if not mentioned",
    "start_date": "YYYY-MM-DD or null if not mentioned",
    "duration": "duration string (e.g., '3 months', '6 months', 'Full-time') or null",
    "compensation": "salary/stipend amount or null",
    "requirements": ["list", "of", "requirements"],
    "skills": ["list", "of", "required", "skills"],
    "description": "brief description (max 500 chars)",
    "apply_url": "application URL or same as source URL",
    "is_still_open": true or false (guess based on context)
}}

Rules:
- Extract ONLY information that is clearly present in the content
- Use null for missing information (do NOT guess or make up data)
- For skills, extract technical skills, programming languages, tools
- Keep description concise but informative
- Ensure all dates are in YYYY-MM-DD format
- If type is unclear, default to "job"
"""
    
    def _validate_and_clean(self, data: Dict, url: str) -> Optional[Dict]:
        """
        Validate and clean the parsed data.
        
        Args:
            data: Parsed data from GPT-4
            url: Source URL
            
        Returns:
            Cleaned and validated opportunity dict or None
        """
        try:
            # Required fields
            if not data.get('title') or not data.get('company'):
                logger.warning(f"Missing required fields for {url}")
                return None
            
            # Build cleaned opportunity
            opportunity = {
                'title': str(data.get('title', '')).strip(),
                'company': str(data.get('company', '')).strip(),
                'type': data.get('type', 'job').lower(),
                'location': data.get('location'),
                'remote': bool(data.get('remote', False)),
                'deadline': data.get('deadline'),
                'start_date': data.get('start_date'),
                'duration': data.get('duration'),
                'compensation': data.get('compensation'),
                'requirements': data.get('requirements', []),
                'skills': data.get('skills', []),
                'description': data.get('description', '')[:500],  # Limit length
                'apply_url': data.get('apply_url') or url,
                'is_still_open': bool(data.get('is_still_open', True)),
                'source_url': url,
            }
            
            # Validate type
            valid_types = ['job', 'internship', 'scholarship', 'fellowship', 'grant']
            if opportunity['type'] not in valid_types:
                opportunity['type'] = 'job'
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Validation error for {url}: {str(e)}")
            return None
    
    def _fallback_parse(self, html: str, url: str) -> Optional[Dict]:
        """
        Simple regex/rule-based fallback parser when GPT-4 fails.
        
        Args:
            html: Raw HTML content
            url: Source URL
            
        Returns:
            Basic opportunity dict or None
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Try to extract basic info with common patterns
            title = None
            company = None
            
            # Common title patterns
            for selector in ['h1', '.job-title', '.title', '#job-title']:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    break
            
            # Common company patterns
            for selector in ['.company', '.company-name', '#company-name']:
                elem = soup.select_one(selector)
                if elem:
                    company = elem.get_text(strip=True)
                    break
            
            if title and company:
                logger.info(f"✅ Fallback parse successful for: {title}")
                return {
                    'title': title,
                    'company': company,
                    'type': 'job',
                    'location': None,
                    'remote': False,
                    'deadline': None,
                    'start_date': None,
                    'duration': None,
                    'compensation': None,
                    'requirements': [],
                    'skills': [],
                    'description': '',
                    'apply_url': url,
                    'is_still_open': True,
                    'source_url': url,
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Fallback parse error for {url}: {str(e)}")
            return None
