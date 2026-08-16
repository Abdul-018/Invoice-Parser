from pydantic import BaseModel, Field 
from typing import List, Optional
from datetime import date

class LineItem(BaseModel):
    """Schema for individual itemised billing breakdown"""
    description: str = Field(description="Description of the item, service, fuel or toll")
    quantity: Optional[float] = Field(default=1.0, description="Quantity billed")
    unit_price: Optional[float] = Field(default=None, description="The price of each unit")
    total_price: float = Field(description="The total price of the products")