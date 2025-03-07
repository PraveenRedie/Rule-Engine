from sqlalchemy import Column, String, Integer, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Attribute(Base):
    __tablename__ = "attributes"

    name = Column(String, primary_key=True, index=True)
    attr_type = Column(String, nullable=False)  # One of: "integer", "float", "boolean", "string"
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    allowed_values = Column(Text, nullable=True)  # JSON string of allowed values for string attributes

class Rule(Base):
    __tablename__ = "rules"

    name = Column(String, primary_key=True, index=True)
    rule_str = Column(Text, nullable=False)