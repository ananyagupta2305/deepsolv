# Shopify Store Insights Fetcher

A FastAPI backend + Streamlit frontend app that scrapes Shopify stores for deep insights.

## ✅ Features
🔍 Scrapes any Shopify store (without API)
📦 Extracts product catalog, hero products, policies, FAQs
🌐 Finds social media & contact info
👥 Competitor analysis with same insights
💾 Stores structured data in MySQL (not raw JSON)
🖥️ Beautiful Streamlit UI with tabs, search, export
🚀 Deployed on Streamlit Cloud


<img width="765" height="382" alt="image" src="https://github.com/user-attachments/assets/a0e58a10-9935-41d9-bedd-2ac90ff46a98" />

## Tech Stack
- Python, FastAPI, MySQL, BeautifulSoup
- Streamlit (UI), Render (Deployment)

## Demo
🌐 [Live Demo (Streamlit)](https://yourname-shopify.streamlit.app)
🔗 [API Endpoint](https://shopify-insights-api.onrender.com/insights)

## How to Run Locally
1. `pip install -r requirements.txt`
2. `uvicorn main:app --reload`
3. `streamlit run frontend.py`

## Screenshots

![Streamlit UI](screenshot.png)

