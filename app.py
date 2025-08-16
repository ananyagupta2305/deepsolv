

# app.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from scraper import scrape_shopify_store
from database import SessionLocal, BrandData, CompetitorData
from sqlalchemy.orm import Session
from competitor import get_competitors
import json
from fastapi.responses import Response

app = FastAPI(title="Shopify Insights Fetcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UrlRequest(BaseModel):
    website_url: str
    include_competitors: Optional[bool] = False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/insights")
def get_insights(request: UrlRequest, db: Session = Depends(get_db)):
    try:
        result = scrape_shopify_store(request.website_url)
        if "error" in result:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])

        # Save to DB
        existing = db.query(BrandData).filter(BrandData.website == result["website"]).first()
        if existing:
            existing.data = json.dumps(result)
        else:
            db.add(BrandData(website=result["website"], data=json.dumps(result)))
        db.commit()

        response_data = {"brand": result}

        if request.include_competitors:
            comp_data = []
            for comp_url in get_competitors(request.website_url):
                comp_result = scrape_shopify_store(comp_url)
                if "error" not in comp_result:
                    # Check if competitor already exists
                    existing_comp = db.query(CompetitorData).filter(
                        CompetitorData.brand_website == result["website"],
                        CompetitorData.competitor_website == comp_result["website"]
                    ).first()
                    
                    if existing_comp:
                        existing_comp.data = json.dumps(comp_result)
                    else:
                        db.add(CompetitorData(
                            brand_website=result["website"],
                            competitor_website=comp_result["website"],
                            data=json.dumps(comp_result)
                        ))
                    comp_data.append(comp_result)
            db.commit()
            response_data["competitors"] = comp_data

        # Return proper JSON response
        return Response(
            content=json.dumps(response_data, indent=2, ensure_ascii=False),
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/brands")
def get_all_brands(db: Session = Depends(get_db)):
    """Get all stored brand data"""
    brands = db.query(BrandData).all()
    return [
        {
            "id": brand.id,
            "website": brand.website,
            "data": json.loads(brand.data) if brand.data else {}
        }
        for brand in brands
    ]

@app.get("/competitors/{brand_website}")
def get_competitors_for_brand(brand_website: str, db: Session = Depends(get_db)):
    """Get all competitors for a specific brand"""
    competitors = db.query(CompetitorData).filter(
        CompetitorData.brand_website == brand_website
    ).all()
    return [
        {
            "id": comp.id,
            "brand_website": comp.brand_website,
            "competitor_website": comp.competitor_website,
            "data": json.loads(comp.data) if comp.data else {}
        }
        for comp in competitors
    ]