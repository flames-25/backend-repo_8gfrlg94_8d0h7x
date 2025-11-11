"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Lead schema for A Plus Charge enquiries
class Lead(BaseModel):
    """
    Leads collection schema
    Collection name: "lead"
    """
    name: str = Field(..., min_length=2, description="Full name of the enquirer")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    company: Optional[str] = Field(None, description="Company/Organization (optional)")
    message: Optional[str] = Field(None, max_length=2000, description="Message or enquiry details")
    city: Optional[str] = Field(None, description="City of the enquirer")
    state: Optional[str] = Field(None, description="State/region")
    country: Optional[str] = Field("India", description="Country, defaults to India")
    source: Optional[str] = Field("website", description="Lead source")
    utm_source: Optional[str] = Field(None, description="UTM source if available")
    utm_medium: Optional[str] = Field(None, description="UTM medium if available")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign if available")
