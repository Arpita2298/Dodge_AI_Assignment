import sqlite3
import json
import os
import glob

DB_PATH = "data.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_jsonl_folder(conn, folder_path, table_name):
    """Ek folder ke saare .jsonl files padhke SQLite mein load karo"""
    all_records = []
    
    # Folder ke andar saari .jsonl files dhundo
    pattern = os.path.join(folder_path, "*.jsonl")
    files = glob.glob(pattern)
    
    if not files:
        print(f"  No .jsonl files found in {folder_path}")
        return
    
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                    except json.JSONDecodeError:
                        continue
    
    if not all_records:
        return
    
    # Saare keys collect karo (columns)
    all_keys = set()
    for record in all_records:
        all_keys.update(record.keys())
    all_keys = list(all_keys)
    
    # Table banao
    columns = ", ".join([f'"{k}" TEXT' for k in all_keys])
    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f'CREATE TABLE "{table_name}" ({columns})')
    
    # Data insert karo
    placeholders = ", ".join(["?" for _ in all_keys])
    col_names = ", ".join([f'"{k}"' for k in all_keys])
    
    for record in all_records:
        values = [str(record.get(k, "")) for k in all_keys]
        conn.execute(
            f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})',
            values
        )
    
    conn.commit()
    print(f"  ✅ {table_name}: {len(all_records)} records loaded")

def init_database():
    """Saara data SQLite mein load karo"""
    print("🔄 Database initialize ho raha hai...")
    
    conn = get_connection()
    
    # Data folder path
    base_path = os.path.join(os.path.dirname(__file__), "data")
    
    # Har folder ke liye table banao
    folders = {
        "billing_document_cancellations": "billing_cancellations",
        "billing_document_headers": "billing_headers",
        "billing_document_items": "billing_items",
        "business_partner_addresses": "bp_addresses",
        "business_partners": "business_partners",
        "customer_company_assignments": "customer_company",
        "customer_sales_area_assignments": "customer_sales_area",
        "journal_entry_items_accounts_receivable": "journal_entries",
        "outbound_delivery_headers": "delivery_headers",
        "outbound_delivery_items": "delivery_items",
        "payments_accounts_receivable": "payments",
        "plants": "plants",
        "product_descriptions": "product_descriptions",
        "product_plants": "product_plants",
        "product_storage_locations": "product_storage",
        "products": "products",
        "sales_order_headers": "sales_order_headers",
        "sales_order_items": "sales_order_items",
        "sales_order_schedule_lines": "sales_order_schedule_lines",
    }
    
    for folder_name, table_name in folders.items():
        folder_path = os.path.join(base_path, folder_name)
        if os.path.exists(folder_path):
            print(f"Loading {folder_name}...")
            load_jsonl_folder(conn, folder_path, table_name)
        else:
            print(f"  ⚠️  Folder not found: {folder_name}")
    
    conn.close()
    print("✅ Database ready!")

def get_table_info():
    """Saari tables aur unke columns return karo"""
    conn = get_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_info = {}
    for table in tables:
        cursor = conn.execute(f'PRAGMA table_info("{table}")')
        columns = [row[1] for row in cursor.fetchall()]
        
        cursor = conn.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        
        table_info[table] = {
            "columns": columns,
            "row_count": count
        }
    
    conn.close()
    return table_info

if __name__ == "__main__":
    init_database()
    info = get_table_info()
    for table, details in info.items():
        print(f"{table}: {details['row_count']} rows, {len(details['columns'])} columns")