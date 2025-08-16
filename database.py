
# database.py
from sqlalchemy import create_engine, Column, Integer, String, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://shopify_user:1234@localhost:3306/shopify_db"
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BrandData(Base):
    __tablename__ = "brand_data"
    id = Column(Integer, primary_key=True, index=True)
    website = Column(String(255), unique=True, index=True)
    data = Column(Text)  # Use Text for large JSON

class CompetitorData(Base):
    __tablename__ = "competitor_data"
    id = Column(Integer, primary_key=True, index=True)
    brand_website = Column(String(255), index=True)
    competitor_website = Column(String(255))
    data = Column(Text)

Base.metadata.create_all(bind=engine)