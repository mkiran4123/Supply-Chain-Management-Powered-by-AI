from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
try:
    # Get Azure OpenAI configuration from environment variables
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")  # Updated to a stable version
    
    if not azure_api_key or not azure_endpoint or not azure_deployment:
        print("Warning: Azure OpenAI configuration not found in environment variables")
        azure_api_key = "your-azure-openai-api-key"  # Placeholder for testing
        azure_endpoint = "https://your-resource-name.openai.azure.com/"  # Placeholder
        azure_deployment = "your-deployment-name"  # Placeholder
        azure_api_version = "2023-05-15"  # Default API version
    
    # Configure Azure OpenAI client
    client = AzureOpenAI(
        api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        api_version=azure_api_version
    )
    print("Azure OpenAI client initialized successfully")
except Exception as e:
    print(f"Error initializing Azure OpenAI client: {str(e)}")
    print("API calls will likely fail without valid Azure OpenAI configuration")

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
    Convert natural language query to SQL using OpenAI API
    """
    
    try:
        # Prepare the prompt for OpenAI
        system_message = f"""You are a SQL expert. Convert the following natural language query into a SQL query for a supply chain management system.
Use the following database schema information:

{DB_SCHEMA}

Only return the SQL query without any explanations or markdown formatting.
The query must be a SELECT statement for security reasons."""
        
        user_message = f"Convert to SQL: {query_text}"
        
        # Check if Azure OpenAI configuration is available
        if not azure_api_key or azure_api_key == "your-azure-openai-api-key":
            print("Azure OpenAI API key not properly configured")
            raise ValueError("Azure OpenAI API key not properly configured")
        
        # Generate SQL using Azure OpenAI API
        print("Generating SQL using Azure OpenAI API")
        
        try:
            # Make API call to Azure OpenAI
            response = client.chat.completions.create(
                deployment_name=azure_deployment,  # Use the deployment name instead of model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Lower temperature for more deterministic outputs
                max_tokens=500,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
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
            print(f"Azure OpenAI API call failed with error: {str(api_error)}")
            raise ValueError(f"Azure OpenAI API call failed: {str(api_error)}")
        
        # Validate the SQL query
        if not sql_query or len(sql_query) < 10:  # Basic length check
            print("Extracted SQL query is too short or empty")
            raise ValueError("OpenAI returned an invalid SQL query")
        
        # Basic validation to ensure it's a SELECT query (for safety)
        if not sql_query.lower().startswith("select"):
            print(f"Query doesn't start with SELECT: {sql_query}")
            raise ValueError("Generated query is not a SELECT statement. For security reasons, only SELECT queries are allowed.")
        
        return sql_query
    
    except Exception as e:
        print(f"Error in generate_sql_from_text: {str(e)}")
        raise Exception(f"Error generating SQL from text: {str(e)}")

def execute_sql_query(db: Session, sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute the generated SQL query and return the results
    """
    try:
        # Execute the query
        result = db.execute(text(sql_query))
        
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

def generate_fallback_sql_query(query_text: str) -> str:
    """
    Generate a simple SQL query based on keywords in the natural language query
    This is a fallback mechanism when the OpenAI API is not available
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

def process_natural_language_query(db: Session, query_text: str) -> Dict[str, Any]:
    """
    Process a natural language query by converting it to SQL and executing it
    """
    try:
        # Generate SQL from natural language
        try:
            sql_query = generate_sql_from_text(query_text)
        except Exception as sql_gen_error:
            print(f"SQL generation failed: {str(sql_gen_error)}, using fallback")
            sql_query = generate_fallback_sql_query(query_text)
            
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