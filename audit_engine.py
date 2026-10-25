import os
import pandas as pd
from sqlalchemy import create_engine

def get_engine(host=None):
    db_host = host or os.getenv("DB_HOST", "postgres_db")
    db_name = os.getenv("DB_NAME", "transaction_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "secretpassword")
    db_port = os.getenv("DB_PORT", "5432")
    
    return create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

def run_sequence_gap_audit(engine):
    query = """
        WITH ordered_tx AS (
            SELECT transaction_id, 
                   LEAD(transaction_id) OVER (ORDER BY transaction_id) AS next_id
            FROM ledger_transactions
        )
        SELECT transaction_id AS current_id, next_id, (next_id - transaction_id - 1) as missing_count
        FROM ordered_tx
        WHERE next_id - transaction_id > 1;
    """
    return pd.read_sql(query, engine)

def run_off_hours_audit(engine):
    query = """
        SELECT transaction_id, account_id, amount, transaction_timestamp, status
        FROM ledger_transactions
        WHERE EXTRACT(HOUR FROM transaction_timestamp) BETWEEN 1 AND 4;
    """
    return pd.read_sql(query, engine)

def run_duplicate_audit(engine):
    query = """
        SELECT amount, account_id, COUNT(*) as occurrence_count
        FROM ledger_transactions
        GROUP BY amount, account_id
        HAVING COUNT(*) > 1;
    """
    return pd.read_sql(query, engine)
