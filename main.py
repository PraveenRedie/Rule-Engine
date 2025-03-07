from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.attributes import router as attributes_router
from api.rules import router as rules_router
from api.evaluation import router as evaluation_router
from core.rule_engine import catalog, rule_engine
from database.session import engine
from database import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rule Engine API",
    description="A powerful rule engine API for creating and evaluating business rules",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(attributes_router, prefix="/api/attributes", tags=["attributes"])
app.include_router(rules_router, prefix="/api/rules", tags=["rules"])
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["evaluation"])

# Load saved attributes and rules from database
@app.on_event("startup")
async def startup_db_client():
    from database.session import SessionLocal
    import json
    from core.rule_system import AttributeType, AttributeDefinition

    db = SessionLocal()
    try:
        # Load attributes
        db_attributes = db.query(models.Attribute).all()
        for db_attr in db_attributes:
            attr_def = AttributeDefinition(
                name=db_attr.name,
                attr_type=AttributeType(db_attr.attr_type),
                min_value=db_attr.min_value,
                max_value=db_attr.max_value,
                allowed_values=set(json.loads(db_attr.allowed_values)) if db_attr.allowed_values else None
            )
            catalog.add_attribute(attr_def)
        
        # Load rules
        db_rules = db.query(models.Rule).all()
        for db_rule in db_rules:
            try:
                rule_engine.create_rule(db_rule.name, db_rule.rule_str)
            except Exception as e:
                print(f"Error loading rule {db_rule.name}: {str(e)}")
    except Exception as e:
        print(f"Error during startup: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)