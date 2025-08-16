# models.py
from pydantic import BaseModel
from typing import List, Optional, Dict

class Product(BaseModel):
    title: str
    handle: str
    price: str
    image: Optional[str] = None

class Policy(BaseModel):
    url: str
    content: Optional[str] = None

class FAQ(BaseModel):
    question: str
    answer: str

class SocialHandle(BaseModel):
    platform: str
    url: str

class ContactInfo(BaseModel):
    emails: List[str]
    phones: List[str]

class BrandInsights(BaseModel):
    brand_name: str
    website: str
    products: List[Product]
    hero_products: List[Product]
    privacy_policy: Optional[Policy]
    return_refund_policy: Optional[Policy]
    faqs: List[FAQ]
    social_handles: List[SocialHandle]
    contact_info: ContactInfo
    about_brand: str
    important_links: Dict[str, str]
    additional_insights: Dict[str, bool] = {}