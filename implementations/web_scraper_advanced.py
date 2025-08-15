#!/usr/bin/env python3
"""
Advanced Web Scraper with Stealth Mode and AI Enhancement
Bypasses anti-bot detection and extracts structured data
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

# Note: Install with: pip install playwright playwright-stealth beautifulsoup4
# Then run: playwright install chromium

class StealthWebScraper:
    """
    Advanced web scraper that bypasses detection systems
    """
    
    def __init__(self, headless: bool = True, cache_dir: str = "./scraper_cache"):
        self.headless = headless
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session_data = {}
        
    def scrape_with_js(self, url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape JavaScript-heavy websites with Playwright
        """
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                # Launch browser with stealth settings
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                # Create context with realistic settings
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation', 'notifications']
                )
                
                # Apply stealth patches
                page = context.new_page()
                self._apply_stealth_patches(page)
                
                # Navigate with random delay
                time.sleep(0.5 + (time.time() % 1))  # Random delay
                page.goto(url, wait_until='networkidle')
                
                # Wait for specific element if provided
                if wait_for:
                    page.wait_for_selector(wait_for, timeout=30000)
                
                # Extract data
                result = {
                    'url': url,
                    'title': page.title(),
                    'content': page.content(),
                    'text': page.inner_text('body'),
                    'timestamp': datetime.now().isoformat(),
                    'screenshot': self._capture_screenshot(page, url),
                    'metadata': self._extract_metadata(page)
                }
                
                # Extract structured data
                result['structured_data'] = self._extract_structured_data(page)
                
                browser.close()
                
                # Cache the result
                self._cache_result(url, result)
                
                return result
                
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _apply_stealth_patches(self, page):
        """Apply stealth JavaScript patches to avoid detection"""
        stealth_js = """
        // Override navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override chrome detection
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Add plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override language
        Object.defineProperty(navigator, 'language', {
            get: () => 'en-US'
        });
        """
        
        page.add_init_script(stealth_js)
    
    def _extract_structured_data(self, page) -> Dict[str, Any]:
        """Extract structured data from the page"""
        structured_data = {}
        
        # Extract JSON-LD
        json_ld_script = page.query_selector('script[type="application/ld+json"]')
        if json_ld_script:
            try:
                structured_data['json_ld'] = json.loads(json_ld_script.inner_text())
            except:
                pass
        
        # Extract Open Graph tags
        og_tags = {}
        for meta in page.query_selector_all('meta[property^="og:"]'):
            property_name = meta.get_attribute('property')
            content = meta.get_attribute('content')
            if property_name and content:
                og_tags[property_name] = content
        if og_tags:
            structured_data['open_graph'] = og_tags
        
        # Extract Twitter Card
        twitter_tags = {}
        for meta in page.query_selector_all('meta[name^="twitter:"]'):
            name = meta.get_attribute('name')
            content = meta.get_attribute('content')
            if name and content:
                twitter_tags[name] = content
        if twitter_tags:
            structured_data['twitter_card'] = twitter_tags
        
        return structured_data
    
    def _extract_metadata(self, page) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {}
        
        # Extract meta description
        meta_desc = page.query_selector('meta[name="description"]')
        if meta_desc:
            metadata['description'] = meta_desc.get_attribute('content')
        
        # Extract canonical URL
        canonical = page.query_selector('link[rel="canonical"]')
        if canonical:
            metadata['canonical'] = canonical.get_attribute('href')
        
        # Count images, links, etc.
        metadata['stats'] = {
            'images': len(page.query_selector_all('img')),
            'links': len(page.query_selector_all('a')),
            'forms': len(page.query_selector_all('form')),
            'scripts': len(page.query_selector_all('script')),
        }
        
        return metadata
    
    def _capture_screenshot(self, page, url: str) -> str:
        """Capture and save screenshot"""
        filename = hashlib.md5(url.encode()).hexdigest()
        screenshot_path = self.cache_dir / f"{filename}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    
    def _cache_result(self, url: str, result: Dict[str, Any]):
        """Cache scraping result"""
        cache_file = self.cache_dir / f"{hashlib.md5(url.encode()).hexdigest()}.json"
        with open(cache_file, 'w') as f:
            # Remove non-serializable content
            cache_data = {k: v for k, v in result.items() if k != 'content'}
            json.dump(cache_data, f, indent=2)
    
    def scrape_multiple(self, urls: List[str], delay: float = 2.0) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs with delay between requests
        """
        results = []
        for i, url in enumerate(urls):
            print(f"Scraping {i+1}/{len(urls)}: {url}")
            result = self.scrape_with_js(url)
            results.append(result)
            
            if i < len(urls) - 1:
                time.sleep(delay)
        
        return results
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,5}[-\s\.]?[0-9]{3,5}'
        return list(set(re.findall(phone_pattern, text)))
    
    def extract_prices(self, text: str) -> List[str]:
        """Extract prices from text"""
        price_pattern = r'\$[\d,]+\.?\d*|\d+\.\d{2}\s*(USD|EUR|GBP)'
        return list(set(re.findall(price_pattern, text)))


class IntelligentScraper(StealthWebScraper):
    """
    Enhanced scraper with AI-powered content extraction
    """
    
    def extract_article(self, url: str) -> Dict[str, Any]:
        """
        Extract article content intelligently
        """
        data = self.scrape_with_js(url)
        
        if 'error' in data:
            return data
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(data['content'], 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find article content
        article = {}
        
        # Title extraction
        title_candidates = [
            soup.find('h1'),
            soup.find('meta', property='og:title'),
            soup.find('title')
        ]
        for candidate in title_candidates:
            if candidate:
                article['title'] = candidate.get_text() if hasattr(candidate, 'get_text') else candidate.get('content')
                break
        
        # Author extraction
        author_selectors = [
            {'name': 'author'},
            {'property': 'article:author'},
            {'class_': re.compile('author|byline|by-line')}
        ]
        for selector in author_selectors:
            author = soup.find(attrs=selector)
            if author:
                article['author'] = author.get_text() if hasattr(author, 'get_text') else author.get('content')
                break
        
        # Date extraction
        date_selectors = [
            {'property': 'article:published_time'},
            {'name': 'publish_date'},
            {'class_': re.compile('date|time|published')}
        ]
        for selector in date_selectors:
            date = soup.find(attrs=selector)
            if date:
                article['date'] = date.get('content', date.get_text() if hasattr(date, 'get_text') else '')
                break
        
        # Main content extraction
        content_candidates = [
            soup.find('article'),
            soup.find('main'),
            soup.find('div', class_=re.compile('content|article|post')),
            soup.find('div', id=re.compile('content|article|post'))
        ]
        
        for candidate in content_candidates:
            if candidate:
                # Get text and clean it
                text = candidate.get_text(separator='\n', strip=True)
                # Remove excessive whitespace
                text = re.sub(r'\n{3,}', '\n\n', text)
                article['content'] = text
                break
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '')
            if src:
                images.append({'src': src, 'alt': alt})
        article['images'] = images
        
        # Add metadata
        article['url'] = url
        article['scraped_at'] = datetime.now().isoformat()
        
        return article


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Web Scraper")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--article", action="store_true", help="Extract as article")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    if args.article:
        scraper = IntelligentScraper(headless=args.headless)
        result = scraper.extract_article(args.url)
    else:
        scraper = StealthWebScraper(headless=args.headless)
        result = scraper.scrape_with_js(args.url)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    # Print summary
    if 'error' not in result:
        print(f"\n📊 Summary:")
        print(f"  • Title: {result.get('title', 'N/A')}")
        print(f"  • URL: {result.get('url', 'N/A')}")
        if 'metadata' in result and 'stats' in result['metadata']:
            stats = result['metadata']['stats']
            print(f"  • Images: {stats.get('images', 0)}")
            print(f"  • Links: {stats.get('links', 0)}")
        print(f"  • Screenshot: {result.get('screenshot', 'N/A')}")
