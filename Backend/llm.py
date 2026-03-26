from groq import Groq
import sqlite3
import os

from dotenv import load_dotenv
load_dotenv()


from database import get_connection, get_table_info

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  

client = Groq(api_key=GROQ_API_KEY)


MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a data analyst for an Order-to-Cash business system.
You have access to a SQLite database with these tables:

- sales_order_headers: salesOrder, soldToParty, salesOrderType, creationDate, totalNetAmount, transactionCurrency, overallDeliveryStatus, overallOrdReltdBillgStatus
- sales_order_items: salesOrder, salesOrderItem, material, requestedQuantity, netAmount
- delivery_headers: deliveryDocument, creationDate, overallGoodsMovementStatus, actualGoodsMovementDate
- delivery_items: deliveryDocument, deliveryDocumentItem, referenceSdDocument, referenceSdDocumentItem, actualDeliveryQuantity, plant
- billing_headers: billingDocument, soldToParty, accountingDocument, billingDocumentDate, totalNetAmount, transactionCurrency, billingDocumentType, billingDocumentIsCancelled
- billing_items: billingDocument, billingDocumentItem, referenceSdDocument, material, billingQuantity, netAmount
- payments: accountingDocument, invoiceReference, salesDocument, amountInTransactionCurrency, transactionCurrency, postingDate, customer
- journal_entries: accountingDocument, referenceDocument, postingDate, amountInTransactionCurrency, transactionCurrency, companyCode
- business_partners: businessPartner, businessPartnerFullName, businessPartnerCategory, customer
- products: product, productType, baseUnit, productGroup

RULES:
1. ONLY answer questions about this Order-to-Cash dataset
2. For data questions, generate a SQL query first
3. Always respond in this exact format:

SQL: <your sql query here>
ANSWER: <your natural language answer here>

4. If question is NOT related to this dataset, respond exactly:
SQL: NONE
ANSWER: This system is designed to answer questions related to the Order-to-Cash dataset only.

5. Keep SQL simple and valid for SQLite
6. Never make up data - only use what the database returns
"""

def is_relevant_query(question: str) -> bool:
    irrelevant_keywords = [
        "weather", "joke", "poem", "story", "capital of",
        "who is president", "recipe", "movie", "sport",
        "cricket", "football", "news", "politics"
    ]
    q_lower = question.lower()
    return not any(kw in q_lower for kw in irrelevant_keywords)

def execute_sql(sql: str):
    try:
        conn = get_connection()
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "No data found."
        result = []
        for row in rows[:20]:
            row_dict = dict(zip(columns, row))
            result.append(row_dict)
        return result
    except Exception as e:
        return f"SQL Error: {str(e)}"

def chat(question: str, history: list = None):
    if history is None:
        history = []
    if not is_relevant_query(question):
        return {
            "answer": "This system is designed to answer questions related to the Order-to-Cash dataset only.",
            "sql": None,
            "data": None
        }

    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {question}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": full_prompt}]
        )
        response_text = response.choices[0].message.content

        sql = None
        answer = response_text

        if "SQL:" in response_text and "ANSWER:" in response_text:
            parts = response_text.split("ANSWER:")
            sql_part = parts[0].replace("SQL:", "").strip()
            answer = parts[1].strip()

            if sql_part and sql_part != "NONE":
                sql = sql_part
                data = execute_sql(sql)

                if isinstance(data, list) and len(data) > 0:
                    data_prompt = f"""
{SYSTEM_PROMPT}

User Question: {question}

I ran this SQL query: {sql}

The database returned this data: {str(data[:10])}

Now give a clear, concise natural language answer based on this actual data.
Do not include SQL in your response, just the answer.
"""
                    final_response = client.chat.completions.create(
                        model=MODEL,
                        messages=[{"role": "user", "content": data_prompt}]
                    )
                    answer = final_response.choices[0].message.content
                    return {"answer": answer, "sql": sql, "data": data}
                else:
                    return {"answer": answer, "sql": sql, "data": data}

        return {"answer": answer, "sql": None, "data": None}

    except Exception as e:
        return {
            "answer": f"Error processing query: {str(e)}",
            "sql": None,
            "data": None
        }


if __name__ == "__main__":
    result = chat("How many sales orders are there?")
    print("SQL:", result["sql"])
    print("Answer:", result["answer"])