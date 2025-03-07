from typing import List
from pydantic import BaseModel, Field

class RuleBase(BaseModel):
    name: str
    rule_str: str

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    rule_str: str

class Rule(RuleBase):
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "adult_us_citizen",
                "rule_str": "(age >= 18) AND (country = 'US')"
            }
        }

class RuleCombine(BaseModel):
    new_rule_name: str
    rule_names: List[str]
    operator: str = Field(..., description="Must be 'and' or 'or'")
    
    class Config:
        schema_extra = {
            "example": {
                "new_rule_name": "combined_rule",
                "rule_names": ["rule1", "rule2"],
                "operator": "and"
            }
        }