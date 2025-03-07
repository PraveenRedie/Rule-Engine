from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from database import models
from schemas import rule as schemas
from core.rule_system import ParseError
from core.rule_engine import rule_engine

router = APIRouter()

@router.post("/", response_model=schemas.Rule, status_code=status.HTTP_201_CREATED)
def create_rule(rule: schemas.RuleCreate, db: Session = Depends(get_db)):
    """
    Create a new rule.
    
    Rules use the following syntax:
    - Simple condition: attribute operator value
    - Logical operations: AND, OR, NOT
    - Parentheses for grouping
    
    Example: (age > 18) AND (country = 'US' OR country = 'CA')
    """
    # Check if rule already exists
    db_rule = db.query(models.Rule).filter(models.Rule.name == rule.name).first()
    if db_rule:
        raise HTTPException(status_code=400, detail="Rule already exists")
    
    try:
        # Create rule in memory
        created_rule = rule_engine.create_rule(rule.name, rule.rule_str)
        
        # Create rule in database
        db_rule = models.Rule(
            name=rule.name,
            rule_str=rule.rule_str
        )
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except ParseError as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.Rule])
def get_rules(db: Session = Depends(get_db)):
    """
    Get all rules.
    """
    return db.query(models.Rule).all()

@router.get("/{rule_name}", response_model=schemas.Rule)
def get_rule(rule_name: str, db: Session = Depends(get_db)):
    """
    Get a specific rule by name.
    """
    db_rule = db.query(models.Rule).filter(models.Rule.name == rule_name).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return db_rule

@router.put("/{rule_name}", response_model=schemas.Rule)
def update_rule(rule_name: str, rule: schemas.RuleUpdate, db: Session = Depends(get_db)):
    """
    Update an existing rule.
    """
    db_rule = db.query(models.Rule).filter(models.Rule.name == rule_name).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    try:
        # Update rule in memory
        updated_rule = rule_engine.modify_rule(rule_name, rule.rule_str)
        
        # Update rule in database
        db_rule.rule_str = rule.rule_str
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except ParseError as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{rule_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_name: str, db: Session = Depends(get_db)):
    """
    Delete a rule by name.
    """
    db_rule = db.query(models.Rule).filter(models.Rule.name == rule_name).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Delete from rule engine and database
    if rule_name in rule_engine.rules:
        del rule_engine.rules[rule_name]
    
    db.delete(db_rule)
    db.commit()
    return None

@router.post("/combine/", response_model=schemas.Rule, status_code=status.HTTP_201_CREATED)
def combine_rules(combine_data: schemas.RuleCombine, db: Session = Depends(get_db)):
    """
    Combine multiple rules with a logical operator.
    
    This allows you to create complex rules by combining existing ones.
    """
    # Check if new rule name already exists
    db_rule = db.query(models.Rule).filter(models.Rule.name == combine_data.new_rule_name).first()
    if db_rule:
        raise HTTPException(status_code=400, detail="Rule with this name already exists")
    
    try:
        # Combine rules in memory
        combined_rule = rule_engine.combine_rules(
            combine_data.new_rule_name, 
            combine_data.rule_names, 
            combine_data.operator
        )
        
        # Create combined rule in database
        db_rule = models.Rule(
            name=combined_rule.name,
            rule_str=combined_rule.rule_str
        )
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))