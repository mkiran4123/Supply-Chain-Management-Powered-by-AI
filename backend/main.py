from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import base64
from openai import AzureOpenAI

# Import app modules
from app import models, schemas, crud
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES

# Initialize FastAPI app
app = FastAPI(title="Supply Chain Management API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from React frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
try:
    # Get Azure OpenAI configuration from environment variables
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "Get This From Azure")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://test-aipractice-openai.openai.azure.com/")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo-16k")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")  # Updated to a stable version

    client = AzureOpenAI(
        api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        api_version=azure_api_version
    )
    print("Azure OpenAI client initialized successfully")
except Exception as e:
    print(f"Error initializing Azure OpenAI client: {str(e)}")
    print("API calls will likely fail without a valid Azure OpenAI configuration")

# Database schema information for context
DB_SCHEMA = """
Tables:
1. inventory
   - id (int, primary key)
   - product_name (string, indexed)
   - description (string)
   - quantity (int)
   - unit_price (float)
   - category (string, indexed)
   - location (string)
   - last_updated (datetime)

2. suppliers
   - id (int, primary key)
   - name (string, indexed)
   - contact_name (string)
   - email (string)
   - phone (string)
   - address (string)
   - is_active (boolean)

3. orders
   - id (int, primary key)
   - order_date (datetime)
   - status (string, indexed) - values: pending, completed, cancelled
   - total_amount (float)
   - supplier_id (int, foreign key to suppliers.id)

4. order_items
   - id (int, primary key)
   - order_id (int, foreign key to orders.id)
   - inventory_id (int, foreign key to inventory.id)
   - quantity (int)
   - unit_price (float)

5. users
   - id (int, primary key)
   - email (string, unique, indexed)
   - hashed_password (string)
   - full_name (string)
   - is_active (boolean)

6. activity_logs
   - id (int, primary key)
   - user_id (int, foreign key to users.id)
   - action (string)
   - entity_type (string) - values: inventory, order, supplier
   - entity_id (int)
   - details (text)
   - timestamp (datetime)
"""

def generate_sql_from_text(query_text: str) -> str:
    """
    Convert natural language query to SQL using Azure OpenAI API
    If API call fails, use a rule-based fallback approach
    """
    
    try:
        # Prepare the prompt for OpenAI
        system_message = f"""You are a SQL expert. Convert the following natural language query into a SQL query for a supply chain management system.
Use the following database schema information:

{DB_SCHEMA}

Only return the SQL query without any explanations or markdown formatting.
The query must be a SELECT statement for security reasons."""
        
        user_message = f"Convert to SQL: {query_text}"
        
        # Check if Azure OpenAI API key is available
        if not azure_api_key or azure_api_key == "your-azure-openai-api-key":
            print("Azure OpenAI API key not properly configured, using rule-based fallback")
            return generate_fallback_sql_query(query_text)
        
        # Generate SQL using Azure OpenAI API
        print("Generating SQL using Azure OpenAI API")
        
        try:
            # Make API call to Azure OpenAI
            response = client.chat.completions.create(
                model=azure_deployment,  # Use deployment_name for Azure OpenAI
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Lower temperature for more deterministic outputs
                max_tokens=500,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,  
                stream=False
            )
            
            # Extract the SQL query from the response
            sql_query = response.choices[0].message.content.strip()
            print(f"Generated SQL query: {sql_query}")
            
            # Clean up any additional text that might be included
            # Look for SQL keywords to identify the start of the query
            sql_keywords = ["SELECT", "select"]
            for keyword in sql_keywords:
                if keyword in sql_query:
                    sql_query = sql_query[sql_query.find(keyword):]
                    break
            
            # Add semicolon if missing
            if not sql_query.endswith(";"):
                sql_query += ";"
            
            print(f"SQL query extracted (length: {len(sql_query)}): {sql_query}")
        except Exception as api_error:
            print(f"Azure OpenAI API call failed with error: {str(api_error)}, using rule-based fallback")
            return generate_fallback_sql_query(query_text)
        
        # Validate the SQL query
        if not sql_query or len(sql_query) < 10:  # Basic length check
            print("Extracted SQL query is too short or empty, using rule-based fallback")
            return generate_fallback_sql_query(query_text)
        
        # Basic validation to ensure it's a SELECT query (for safety)
        if not sql_query.lower().startswith("select"):
            print(f"Query doesn't start with SELECT: {sql_query}, using rule-based fallback")
            return generate_fallback_sql_query(query_text)
        
        return sql_query
    
    except Exception as e:
        print(f"Error in generate_sql_from_text: {str(e)}, using rule-based fallback")
        return generate_fallback_sql_query(query_text)

def generate_fallback_sql_query(query_text: str) -> str:
    """
    Generate a simple SQL query based on keywords in the natural language query
    This is a fallback mechanism when the LLM is not available
    """
    query_lower = query_text.lower()
    
    # Default query - return a limited set of inventory items
    default_query = "SELECT * FROM inventory LIMIT 10;"
    
    # Check for specific entity types in the query
    if any(word in query_lower for word in ["inventory", "product", "item", "stock"]):
        if "low" in query_lower or "out of" in query_lower:
            return "SELECT * FROM inventory WHERE quantity < 10 ORDER BY quantity ASC;"
        elif "expensive" in query_lower or "highest price" in query_lower:
            return "SELECT * FROM inventory ORDER BY unit_price DESC LIMIT 10;"
        elif "cheap" in query_lower or "lowest price" in query_lower:
            return "SELECT * FROM inventory ORDER BY unit_price ASC LIMIT 10;"
        else:
            return "SELECT * FROM inventory LIMIT 20;"
    
    elif any(word in query_lower for word in ["supplier", "vendor", "provider"]):
        if "active" in query_lower:
            return "SELECT * FROM suppliers WHERE is_active = TRUE;"
        else:
            return "SELECT * FROM suppliers LIMIT 20;"
    
    elif any(word in query_lower for word in ["order", "purchase"]):
        if "pending" in query_lower:
            return "SELECT * FROM orders WHERE status = 'pending';"
        elif "completed" in query_lower:
            return "SELECT * FROM orders WHERE status = 'completed';"
        elif "cancelled" in query_lower or "canceled" in query_lower:
            return "SELECT * FROM orders WHERE status = 'cancelled';"
        else:
            return "SELECT * FROM orders LIMIT 20;"
    
    elif any(word in query_lower for word in ["user", "account"]):
        return "SELECT id, email, full_name, is_active FROM users LIMIT 20;"
    
    # If we can't determine the intent, return a default query
    print(f"Could not determine specific intent from query: '{query_text}', using default query")
    return default_query

def execute_sql_query(db: Session, sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute the generated SQL query and return the results
    """
    try:
        # Execute the query
        print("execute_sql_query : "+ sql_query)
        result = db.execute(text(sql_query))
        
        print("SQL query executed successfully, processing results...")
        # Convert the result to a list of dictionaries
        column_names = result.keys()
        rows = result.fetchall()
        
        # Format the results
        formatted_results = [
            {column: value for column, value in zip(column_names, row)}
            for row in rows
        ]
        
        return formatted_results
    
    except Exception as e:
        raise Exception(f"Error executing SQL query: {str(e)}")

def process_natural_language_query(db: Session, query_text: str) -> Dict[str, Any]:
    """
    Process a natural language query by converting it to SQL and executing it
    """
    print("process_natural_language_query: " + query_text)
    try:
        # Generate SQL from natural language
        sql_query = generate_sql_from_text(query_text)
        # Execute the SQL query
        results = execute_sql_query(db, sql_query)
        
        return {
            "success": True,
            "query": query_text,
            "sql": sql_query,
            "results": results
        }
    
    except Exception as e:
        return {
            "success": False,
            "query": query_text,
            "error": str(e)
        }

# AI-powered search endpoint (Natural Language to SQL)
@app.post("/ai/search/", response_model=dict)
def ai_search(query: schemas.NLQueryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    """Process natural language query and return SQL results"""
    result = process_natural_language_query(db, query.query_text)
    return result

# Health check endpoint
@app.get("/health")
def health_check(current_user: models.User = Depends(get_current_active_user)):
    return {
        "success": True,
        "message": "Health check successful"
    }

# Authentication endpoints
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

# User management endpoints
@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Inventory endpoints
@app.get("/inventory/", response_model=List[schemas.Inventory])
def read_inventory(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    inventory = crud.get_inventory(db, skip=skip, limit=limit)
    return inventory

@app.get("/inventory/{inventory_id}", response_model=schemas.Inventory)
def read_inventory_item(inventory_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_inventory = crud.get_inventory_item(db, inventory_id=inventory_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return db_inventory

@app.post("/inventory/", response_model=schemas.Inventory, status_code=status.HTTP_201_CREATED)
def create_inventory_item(inventory: schemas.InventoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return crud.create_inventory_item(db=db, inventory=inventory)

@app.put("/inventory/{inventory_id}", response_model=schemas.Inventory)
def update_inventory_item(inventory_id: int, inventory: schemas.InventoryUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_inventory = crud.get_inventory_item(db, inventory_id=inventory_id)
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return crud.update_inventory_item(db=db, inventory_id=inventory_id, inventory=inventory)

# Supplier endpoints
@app.get("/suppliers/", response_model=List[schemas.Supplier])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
    return suppliers

@app.get("/suppliers/{supplier_id}", response_model=schemas.Supplier)
def read_supplier(supplier_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_supplier = crud.get_supplier(db, supplier_id=supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db_supplier

@app.post("/suppliers/", response_model=schemas.Supplier, status_code=status.HTTP_201_CREATED)
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return crud.create_supplier(db=db, supplier=supplier)

@app.put("/suppliers/{supplier_id}", response_model=schemas.Supplier)
def update_supplier(supplier_id: int, supplier: schemas.SupplierUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_supplier = crud.get_supplier(db, supplier_id=supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return crud.update_supplier(db=db, supplier_id=supplier_id, supplier=supplier)

# Order endpoints
@app.get("/orders/", response_model=List[schemas.Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    orders = crud.get_orders(db, skip=skip, limit=limit)
    return orders

@app.get("/orders/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@app.post("/orders/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return crud.create_order(db=db, order=order)

@app.put("/orders/{order_id}", response_model=schemas.Order)
def update_order(order_id: int, order: schemas.OrderUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return crud.update_order(db=db, order_id=order_id, order=order)

# CSV import/export endpoints (TR3.1)
@app.post("/import/{entity_type}/", status_code=status.HTTP_201_CREATED)
def import_csv(entity_type: str, file: bytes, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    # Implementation would handle different entity types (inventory, orders, suppliers)
    # and process the CSV file accordingly
    return {"message": f"Successfully imported {entity_type} data"}

@app.get("/export/{entity_type}/")
def export_csv(entity_type: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    # Implementation would query the database for the requested entity type
    # and return the data as a CSV file
    return {"message": f"Successfully exported {entity_type} data"}