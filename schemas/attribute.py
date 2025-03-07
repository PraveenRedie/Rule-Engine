from typing import List, Optional, Set
from pydantic import BaseModel, Field

class AttributeBase(BaseModel):
    name: str
    attr_type: str = Field(..., description="One of: integer, float, boolean, string")
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[Set[str]] = None

class AttributeCreate(AttributeBase):
    pass

class AttributeUpdate(BaseModel):
    attr_type: str = Field(..., description="One of: integer, float, boolean, string")
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[Set[str]] = None

class Attribute(AttributeBase):
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "age",
                "attr_type": "integer",
                "min_value": 0,
                "max_value": 120,
                "allowed_values": None
            }
        }