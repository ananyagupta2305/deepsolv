# llm_processor.py
from asyncio.log import logger
from typing import Dict, List
from groq import Groq
import os
import json
import re

client = Groq(api_key="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")

def preprocess_text(text: str) -> str:
    """Clean and preprocess text before sending to LLM"""
    if not text:
        return ""
    
    # Remove excessive whitespace and newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s{3,}', ' ', text)
    
    # Remove common navigation/footer text
    patterns_to_remove = [
        r'Skip to content',
        r'Add to cart',
        r'Quick view',
        r'Search for:',
        r'Copyright.*\d{4}',
        r'All rights reserved',
        r'Follow us on',
        r'Subscribe to our newsletter'
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Limit text length
    return text[:8000].strip()

def clean_policy_text(dirty_text: str) -> str:
    """Extract and clean policy text using LLM"""
    if not dirty_text or len(dirty_text.strip()) < 50:
        return "Not available."
    
    cleaned_text = preprocess_text(dirty_text)
    
    prompt = f"""
You are a legal document processor. Extract and clean the main content from this privacy/return policy.

Instructions:
1. Remove navigation menus, headers, footers, and repeated phrases
2. Extract only the actual policy content
3. Summarize in clear, professional language
4. Keep important details but make it concise (300-500 words)
5. Structure with clear sections if applicable

Raw text:
\"\"\"
{cleaned_text}
\"\"\"

Cleaned policy:"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.2,
            max_tokens=4500
        )
        
        content = chat_completion.choices[0].message.content.strip()
        
        if len(content) < 50:
            logger.warning("LLM returned very short policy content")
            return "Policy content could not be properly extracted."
        
        return content
        
    except Exception as e:
        logger.error(f"Error cleaning policy text: {str(e)}")
        return "Error processing policy text."

def extract_faqs(dirty_text: str) -> List[Dict[str, str]]:
    """Extract FAQ pairs using LLM with better validation"""
    if not dirty_text or len(dirty_text.strip()) < 100:
        logger.info("Text too short for FAQ extraction")
        return []
    
    cleaned_text = preprocess_text(dirty_text)
    
    prompt = f"""
Extract FAQ question-answer pairs from this webpage content.

Rules:
1. Only extract clear, complete question-answer pairs
2. Questions should be customer-focused (shipping, returns, sizing, etc.)
3. Answers should be informative and complete
4. Return ONLY valid JSON array format
5. Maximum 8 FAQs
6. If no clear FAQs exist, return: []

Format: [{{"question": "Question here?", "answer": "Complete answer here."}}]

Webpage content:
\"\"\"
{cleaned_text}
\"\"\"

JSON Response:"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1,
            max_tokens=4500
        )
        
        content = chat_completion.choices[0].message.content.strip()
        logger.info(f"LLM FAQ Response length: {len(content)}")
        
        # More robust JSON extraction
        json_patterns = [
            r'\[.*?\]',  # Simple array pattern
            r'```json\s*(\[.*?\])\s*```',  # JSON code blocks
            r'```\s*(\[.*?\])\s*```'  # Generic code blocks
        ]
        
        json_str = None
        for pattern in json_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                json_str = match.group(1) if match.groups() else match.group(0)
                break
        
        if not json_str:
            logger.warning("No JSON pattern found in LLM response")
            return extract_faqs_fallback(dirty_text)
        
        try:
            faqs = json.loads(json_str)
            
            # Validate structure
            if not isinstance(faqs, list):
                logger.error("LLM returned non-list JSON")
                return extract_faqs_fallback(dirty_text)
            
            validated_faqs = []
            for faq in faqs:
                if (isinstance(faq, dict) and 
                    "question" in faq and 
                    "answer" in faq and
                    len(str(faq["question"]).strip()) > 10 and
                    len(str(faq["answer"]).strip()) > 10):
                    
                    validated_faqs.append({
                        "question": str(faq["question"]).strip(),
                        "answer": str(faq["answer"]).strip()
                    })
            
            logger.info(f"Successfully extracted {len(validated_faqs)} FAQs")
            return validated_faqs[:8]  # Limit to 8 FAQs
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON parsing failed: {je}")
            logger.error(f"Attempted to parse: {json_str[:200]}")
            return extract_faqs_fallback(dirty_text)
            
    except Exception as e:
        logger.error(f"LLM FAQ extraction error: {e}")
        return extract_faqs_fallback(dirty_text)

def extract_faqs_fallback(dirty_text: str) -> List[Dict[str, str]]:
    """Fallback FAQ extraction using pattern matching"""
    logger.info("Using fallback FAQ extraction")
    faqs = []
    
    # Clean the text first
    text = preprocess_text(dirty_text)
    
    # Look for structured FAQ sections
    faq_patterns = [
        # Q: A: format
        r'Q:\s*([^?]+\?)\s*A:\s*([^Q]+?)(?=Q:|$)',
        # Question: Answer: format
        r'Question:\s*([^?]+\?)\s*Answer:\s*([^Q]+?)(?=Question:|$)',
        # FAQ with numbers
        r'\d+\.\s*([^?]+\?)\s*([^0-9]+?)(?=\d+\.|$)',
    ]
    
    for pattern in faq_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        for question, answer in matches:
            q = question.strip()
            a = answer.strip()
            
            if len(q) > 10 and len(a) > 20 and len(a) < 500:
                # Clean up the answer
                a = re.sub(r'\s+', ' ', a)
                a = a[:300] + "..." if len(a) > 300 else a
                
                faqs.append({
                    "question": q,
                    "answer": a
                })
        
        if faqs:
            break
    
    # Try to find common question patterns
    if not faqs:
        question_starters = ['what', 'how', 'when', 'where', 'can', 'do you', 'is']
        for starter in question_starters:
            pattern = rf'({starter}[^?]+\?)\s*([^.]+(?:\.[^.]*?){{1,3}})'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for question, answer in matches[:3]:  # Limit per starter
                q = question.strip()
                a = answer.strip()
                
                if len(q) > 15 and len(a) > 30 and not any(faq['question'].lower() == q.lower() for faq in faqs):
                    faqs.append({
                        "question": q,
                        "answer": a
                    })
    
    return faqs[:6]  # Limit to 6 FAQs

def summarize_about_text(dirty_text: str) -> str:
    """Summarize about/brand text using LLM"""
    if not dirty_text or len(dirty_text.strip()) < 100:
        return "Not available."
    
    cleaned_text = preprocess_text(dirty_text)
    
    prompt = f"""
Create a professional brand summary from this about page content.

Focus on:
1. Brand story and mission
2. What makes them unique
3. Key values or specialties
4. Target audience (if mentioned)

Keep it concise (3-5 sentences) and engaging.

About page content:
\"\"\"
{cleaned_text}
\"\"\"

Brand Summary:"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.4,
            max_tokens=4500
        )
        
        content = chat_completion.choices[0].message.content.strip()
        
        if len(content) < 50:
            logger.warning("LLM returned very short brand summary")
            return "Brand information could not be properly summarized."
        
        return content
        
    except Exception as e:
        logger.error(f"Error summarizing about text: {str(e)}")
        return "Error processing brand information."

def validate_and_enhance_data(scraped_data: dict) -> dict:
    """Final validation and enhancement of scraped data"""
    
    # Ensure all required fields exist
    required_fields = {
        'brand_name': 'Unknown Brand',
        'website': '',
        'products': [],
        'hero_products': [],
        'privacy_policy': None,
        'return_refund_policy': None,
        'faqs': [],
        'social_handles': [],
        'contact_info': {'emails': [], 'phones': []},
        'about_brand': 'Not available.',
        'important_links': {}
    }
    
    for field, default_value in required_fields.items():
        if field not in scraped_data or scraped_data[field] is None:
            scraped_data[field] = default_value
    
    # Validate and clean data
    if scraped_data['products']:
        scraped_data['hero_products'] = scraped_data['products'][:6]  # Ensure we have hero products
    
    # Remove duplicate FAQs
    if scraped_data['faqs']:
        seen_questions = set()
        unique_faqs = []
        for faq in scraped_data['faqs']:
            if faq['question'].lower() not in seen_questions:
                seen_questions.add(faq['question'].lower())
                unique_faqs.append(faq)
        scraped_data['faqs'] = unique_faqs
    
    # Ensure social handles have proper structure
    validated_socials = []
    for social in scraped_data['social_handles']:
        if isinstance(social, dict) and 'platform' in social and 'url' in social:
            validated_socials.append(social)
    scraped_data['social_handles'] = validated_socials
    
    return scraped_data