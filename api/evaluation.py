from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from schemas.evaluation import EvaluationRequest, EvaluationResult, BatchEvaluationRequest, BatchEvaluationResult
from core.rule_engine import rule_engine

router = APIRouter()

@router.post("/{rule_name}", response_model=EvaluationResult)
def evaluate_rule(rule_name: str, request: EvaluationRequest):
    """
    Evaluate a candidate against a specific rule.
    
    This endpoint checks if the provided candidate data satisfies the rule conditions.
    """
    if rule_name not in rule_engine.rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    try:
        result = rule_engine.evaluate(rule_name, request.candidate)
        return {"rule_name": rule_name, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch/{rule_name}", response_model=BatchEvaluationResult)
def batch_evaluate(rule_name: str, request: BatchEvaluationRequest):
    """
    Evaluate multiple candidates against a specific rule.
    
    This is useful for bulk processing of data.
    """
    if rule_name not in rule_engine.rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    results = []
    for i, candidate in enumerate(request.candidates):
        try:
            result = rule_engine.evaluate(rule_name, candidate)
            results.append({"index": i, "result": result, "error": None})
        except ValueError as e:
            results.append({"index": i, "result": False, "error": str(e)})
    
    return {"rule_name": rule_name, "results": results}

@router.post("/multi-rule/", response_model=Dict[str, bool])
def evaluate_multi_rules(rules: List[str], candidate: Dict[str, Any]):
    """
    Evaluate a single candidate against multiple rules.
    
    Returns a dictionary mapping rule names to evaluation results.
    """
    results = {}
    for rule_name in rules:
        if rule_name not in rule_engine.rules:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_name}")
        
        try:
            results[rule_name] = rule_engine.evaluate(rule_name, candidate)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error evaluating rule '{rule_name}': {str(e)}")
    
    return results