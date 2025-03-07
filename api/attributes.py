from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import json

from database.session import get_db
from database import models
from schemas import attribute as schemas
from core.rule_system import AttributeDefinition, AttributeType
from core.rule_engine import catalog

router = APIRouter()

@router.post("/", response_model=schemas.Attribute, status_code=status.HTTP_201_CREATED)
def create_attribute(attribute: schemas.AttributeCreate, db: Session = Depends(get_db)):
    """
    Create a new attribute definition.
    
    This endpoint allows you to define new attributes that can be used in rules.
    """
    # Check if attribute already exists
    db_attribute = db.query(models.Attribute).filter(models.Attribute.name == attribute.name).first()
    if db_attribute:
        raise HTTPException(status_code=400, detail="Attribute already exists")
    
    try:
        # Create attribute in memory
        attr_def = AttributeDefinition(
            name=attribute.name,
            attr_type=AttributeType(attribute.attr_type),
            min_value=attribute.min_value,
            max_value=attribute.max_value,
            allowed_values=set(attribute.allowed_values) if attribute.allowed_values else None
        )
        catalog.add_attribute(attr_def)
        
        # Create attribute in database
        db_attr = models.Attribute(
            name=attribute.name,
            attr_type=attribute.attr_type,
            min_value=attribute.min_value,
            max_value=attribute.max_value,
            allowed_values=json.dumps(list(attribute.allowed_values)) if attribute.allowed_values else None
        )
        db.add(db_attr)
        db.commit()
        db.refresh(db_attr)
        return db_attr
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.Attribute])
def get_attributes(db: Session = Depends(get_db)):
    """
    Get all defined attributes.
    """
    return db.query(models.Attribute).all()

@router.get("/{attribute_name}", response_model=schemas.Attribute)
def get_attribute(attribute_name: str, db: Session = Depends(get_db)):
    """
    Get a specific attribute by name.
    """
    db_attribute = db.query(models.Attribute).filter(models.Attribute.name == attribute_name).first()
    if db_attribute is None:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return db_attribute

@router.put("/{attribute_name}", response_model=schemas.Attribute)
def update_attribute(attribute_name: str, attribute: schemas.AttributeUpdate, db: Session = Depends(get_db)):
    """
    Update an existing attribute.
    """
    db_attribute = db.query(models.Attribute).filter(models.Attribute.name == attribute_name).first()
    if db_attribute is None:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    try:
        # Check if attribute is used in any rule
        db_rules = db.query(models.Rule).all()
        for rule in db_rules:
            if attribute_name in rule.rule_str:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot update attribute used in rule '{rule.name}'. Delete the rule first."
                )
        
        # Update attribute in memory
        if attribute_name in catalog.attributes:
            del catalog.attributes[attribute_name]
        
        attr_def = AttributeDefinition(
            name=attribute_name,
            attr_type=AttributeType(attribute.attr_type),
            min_value=attribute.min_value,
            max_value=attribute.max_value,
            allowed_values=set(attribute.allowed_values) if attribute.allowed_values else None
        )
        catalog.add_attribute(attr_def)
        
        # Update attribute in database
        db_attribute.attr_type = attribute.attr_type
        db_attribute.min_value = attribute.min_value
        db_attribute.max_value = attribute.max_value
        db_attribute.allowed_values = json.dumps(list(attribute.allowed_values)) if attribute.allowed_values else None
        
        db.commit()
        db.refresh(db_attribute)
        return db_attribute
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{attribute_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribute(attribute_name: str, db: Session = Depends(get_db)):
    """
    Delete an attribute by name.
    """
    db_attribute = db.query(models.Attribute).filter(models.Attribute.name == attribute_name).first()
    if db_attribute is None:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    # Check if attribute is used in any rule
    db_rules = db.query(models.Rule).all()
    for rule in db_rules:
        if attribute_name in rule.rule_str:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete attribute used in rule '{rule.name}'. Delete the rule first."
            )
    
    # Delete from catalog and database
    if attribute_name in catalog.attributes:
        del catalog.attributes[attribute_name]
    
    db.delete(db_attribute)
    db.commit()
    return None