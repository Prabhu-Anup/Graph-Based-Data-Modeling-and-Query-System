import os
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

# Load environment entries from .env
load_dotenv()

# Configure the API key securely
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = "YOUR_API_KEY"

genai.configure(api_key=api_key)

# Initialize model
model = genai.GenerativeModel("gemini-2.5-flash")

def generate_sql(user_query: str) -> str:
    prompt = f"""Convert the following natural language query into a SQL query.
Use ONLY the following available tables:
- sales_order
- sales_order_item
- product
- outbound_delivery
- billing_document
- ar_clearing_line

Example Output:
SELECT COUNT(*) FROM sales_order;

Return ONLY SQL (no explanation, no markdown).

Query: {user_query}"""
    response = model.generate_content(prompt)
    
    # Strip any markdown formatting commonly returned by LLMs
    sql = response.text.strip()
    if sql.startswith("```"):
        sql = "\n".join(sql.split("\n")[1:-1])
        
    return sql.strip()

def generate_natural_answer(user_query: str, result: list) -> str:
    prompt = f"""User asked: {user_query}

Database result:
{result}

Convert this into a clear, concise natural language answer.
Do not mention SQL.
Be direct and informative."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return f"Here is the result: {result}"

def handle_query(user_query: str, db: Session):
    generated_sql = generate_sql(user_query)
    
    try:
        result = db.execute(text(generated_sql))
        rows = result.fetchall()
        
        # Return only first 20 rows to avoid overload
        rows = rows[:20]
        
        output = [dict(row._mapping) for row in rows]
        
        answer = generate_natural_answer(user_query, output)
        
        return {
            "answer": answer,
            "generated_sql": generated_sql,
            "result": output
        }
    except Exception as e:
        return {
            "error": str(e),
            "generated_sql": generated_sql
        }
