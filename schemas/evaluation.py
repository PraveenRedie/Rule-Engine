from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class EvaluationRequest(BaseModel):
    candidate: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "candidate": {
                    "age": 25,
                    "country": "US",
                    "income": 60000
                }
            }
        }

class EvaluationResult(BaseModel):
    rule_name: str
    result: bool

class BatchEvaluationRequest(BaseModel):
    candidates: List[Dict[str, Any]]
    
    class Config:
        schema_extra = {
            "example": {
                "candidates": [
                    {"age": 25, "country": "US"},
                    {"age": 17, "country": "US"},
                    {"age": 30, "country": "CA"}
                ]
            }
        }

class BatchResultItem(BaseModel):
    index: int
    result: bool
    error: Optional[str] = None

class BatchEvaluationResult(BaseModel):
    rule_name: str
    results: List[BatchResultItem]