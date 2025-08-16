
#scraper.py
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from models import Product, Policy, FAQ, SocialHandle, ContactInfo
from urllib.parse import urljoin, urlparse
from llm_processor import (
    clean_policy_text, 
    extract_faqs, 
    summarize_about_text, 
    validate_and_enhance_data,
    logger
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_json(url: str) -> dict:
    """Fetch JSON data from URL"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            logger.warning(f"Failed to fetch JSON from {url}: {r.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching JSON from {url}: {e}")
        return {}

def get_soup(url: str) -> Optional[BeautifulSoup]:
    """Fetch and parse HTML from URL"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.content, 'lxml')
        else:
            logger.warning(f"Failed to fetch HTML from {url}: {r.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching HTML from {url}: {e}")
        return None

def extract_clean_text(soup: BeautifulSoup) -> str:
    """Extract clean text from BeautifulSoup object"""
    if not soup:
        return ""
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Get text and clean it
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text

def scrape_shopify_store(base_url: str) -> dict:
    """Main scraping function with improved error handling and data processing"""
    base_url = base_url.strip().rstrip("/")
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    logger.info(f"Starting scrape of: {base_url}")

    # Validate website accessibility
    try:
        res = requests.get(base_url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return {"error": f"Website returned status {res.status_code}", "status_code": res.status_code}
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return {"error": f"Unable to connect: {str(e)}", "status_code": 404}

    soup = get_soup(base_url)
    if not soup:
        return {"error": "Failed to load homepage", "status_code": 500}

    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Products with better error handling
    logger.info("Fetching products...")
    product_json = get_json(f"{base_url}/products.json")
    products = []
    
    for p in product_json.get("products", [])[:50]:  # Limit to 50 products
        try:
            price = "N/A"
            if p.get("variants") and len(p["variants"]) > 0:
                price = p["variants"][0].get("price", "N/A")
            
            image = None
            if p.get("images") and len(p["images"]) > 0:
                image = p["images"][0].get("src")
            
            products.append(Product(
                title=p.get("title", "Unnamed Product"),
                handle=p.get("handle", ""),
                price=str(price),
                image=image
            ).model_dump())
        except Exception as e:
            logger.warning(f"Error processing product: {e}")
            continue

    logger.info(f"Found {len(products)} products")

    # 2. Hero Products (featured on homepage)
    hero_products = []
    try:
        product_links = soup.find_all("a", href=re.compile(r"/products/"))
        seen_handles = set()
        
        for link in product_links:
            if len(hero_products) >= 10:  # Limit hero products
                break
                
            try:
                href = link.get('href', '')
                handle = href.split("/products/")[-1].split("?")[0].split("#")[0]
                
                if handle and handle not in seen_handles:
                    seen_handles.add(handle)
                    matched = [p for p in products if p["handle"] == handle]
                    if matched:
                        hero_products.append(matched[0])
            except Exception as e:
                logger.warning(f"Error processing product link: {e}")
                continue
    except Exception as e:
        logger.error(f"Error finding hero products: {e}")

    # 3. Extract all links with better categorization
    logger.info("Extracting navigation links...")
    links = {}
    try:
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip().lower()
            href = a.get('href', '')
            
            if text and len(text) < 100:  # Avoid very long link texts
                full_url = urljoin(base_url, href)
                links[text] = full_url
    except Exception as e:
        logger.error(f"Error extracting links: {e}")

    # 4. Policy extraction with better URL matching
    def fetch_policy(keywords: List[str]) -> Optional[Dict]:
        """Fetch policy with multiple keyword options"""
        for text, url in links.items():
            if any(keyword in text for keyword in keywords):
                logger.info(f"Found policy page: {url}")
                page_soup = get_soup(url)
                if page_soup:
                    raw_text = extract_clean_text(page_soup)
                    if len(raw_text) > 200:  # Ensure we have substantial content
                        cleaned_content = clean_policy_text(raw_text)
                        return Policy(url=url, content=cleaned_content).model_dump()
        return None

    logger.info("Extracting policies...")
    privacy_policy = fetch_policy(["privacy", "privacy policy", "data protection"])
    refund_policy = fetch_policy(["refund", "return", "returns", "exchange", "refund policy", "return policy"])

    # 5. FAQ extraction with multiple attempts
    logger.info("Extracting FAQs...")
    faqs = []
    
    # Try dedicated FAQ page first
    faq_keywords = ["faq", "frequently asked", "questions", "help", "support"]
    faq_page_found = False
    
    for text, url in links.items():
        if any(keyword in text for keyword in faq_keywords) and not faq_page_found:
            logger.info(f"Found FAQ page: {url}")
            faq_soup = get_soup(url)
            if faq_soup:
                raw_faq_text = extract_clean_text(faq_soup)
                if len(raw_faq_text) > 300:
                    faqs = extract_faqs(raw_faq_text)
                    faq_page_found = True
                    break
    
    # If no dedicated FAQ page, try to extract from main pages
    if not faqs:
        logger.info("No dedicated FAQ page found, trying main content...")
        main_text = extract_clean_text(soup)
        if len(main_text) > 500:
            faqs = extract_faqs(main_text)

    logger.info(f"Found {len(faqs)} FAQs")

    # 6. Social media handles with better validation
    logger.info("Extracting social media links...")
    socials = []
    social_patterns = {
        r'instagram\.com': 'Instagram',
        r'facebook\.com': 'Facebook', 
        r'tiktok\.com': 'TikTok',
        r'twitter\.com': 'Twitter',
        r'youtube\.com': 'YouTube',
        r'linkedin\.com': 'LinkedIn',
        r'pinterest\.com': 'Pinterest'
    }
    
    seen_urls = set()
    
    for a in soup.find_all("a", href=True):
        href = a.get('href', '')
        if href and href not in seen_urls:
            for pattern, platform in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    seen_urls.add(href)
                    socials.append(SocialHandle(platform=platform, url=href).model_dump())
                    break

    # 7. Contact information extraction
    logger.info("Extracting contact information...")
    body_text = extract_clean_text(soup)
    
    # Email extraction with better patterns
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    emails = list(set(re.findall(email_pattern, body_text)))
    
    # Filter out common false positives
    filtered_emails = [email for email in emails 
                      if not any(skip in email.lower() 
                               for skip in ['example.com', 'test@', 'noreply@', 'no-reply@'])]
    
    # Phone extraction with better patterns
    phone_patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
        r'\+?[0-9]{1,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',  # International
    ]
    
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, body_text))
    
    phones = list(set(phones))  # Remove duplicates

    # 8. About brand information
    logger.info("Extracting brand information...")
    about_text = "Not available."
    
    about_keywords = ["about", "our story", "about us", "who we are", "mission"]
    for text, url in links.items():
        if any(keyword in text for keyword in about_keywords):
            about_soup = get_soup(url)
            if about_soup:
                raw_about = extract_clean_text(about_soup)
                if len(raw_about) > 200:
                    about_text = summarize_about_text(raw_about)
                    break

    # 9. Important links categorization
    important_links = {}
    link_categories = {
        "contact_us": ["contact", "contact us", "get in touch"],
        "order_tracking": ["track", "tracking", "track order", "order status"],
        "blog": ["blog", "news", "articles"],
        "shipping": ["shipping", "delivery", "shipping info"],
        "size_guide": ["size", "sizing", "size guide", "fit guide"]
    }
    
    for category, keywords in link_categories.items():
        for text, url in links.items():
            if any(keyword in text for keyword in keywords):
                important_links[category] = url
                break

    # 10. Brand name extraction with fallbacks
    brand_name = "Unknown Brand"
    try:
        # Try title tag first
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            brand_name = title_tag.text.split("|")[0].split("-")[0].strip()
        
        # Try og:site_name meta tag
        if not brand_name or brand_name == "Unknown Brand":
            og_site = soup.find("meta", property="og:site_name")
            if og_site and og_site.get("content"):
                brand_name = og_site["content"].strip()
        
        # Fallback to domain name
        if not brand_name or brand_name == "Unknown Brand":
            brand_name = domain.split("//")[1].split(".")[0].title()
            
    except Exception as e:
        logger.error(f"Error extracting brand name: {e}")

    # Compile final data
    scraped_data = {
        "brand_name": brand_name,
        "website": base_url,
        "products": products,
        "hero_products": hero_products,
        "privacy_policy": privacy_policy,
        "return_refund_policy": refund_policy,
        "faqs": faqs,
        "social_handles": socials,
        "contact_info": {"emails": filtered_emails, "phones": phones},
        "about_brand": about_text,
        "important_links": important_links
    }

    # Final validation and enhancement
    validated_data = validate_and_enhance_data(scraped_data)
    
    logger.info(f"Scraping completed for {brand_name}")
    logger.info(f"Summary: {len(products)} products, {len(faqs)} FAQs, {len(socials)} social links")
    
    return validated_data