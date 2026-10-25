import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "transaction_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secretpassword")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def seed_database():
    with engine.begin() as conn:
        print("Creating transactions table...")
        conn.execute(text("""
            DROP TABLE IF EXISTS ledger_transactions;
            CREATE TABLE ledger_transactions (
                transaction_id INT PRIMARY KEY,
                account_id INT,
                amount NUMERIC(10, 2),
                transaction_timestamp TIMESTAMP,
                status VARCHAR(50)
            );
        """))

        print("Generating dummy data with intentional anomalies...")
        
        base_time = datetime.now() - timedelta(days=5)
        records = []
        
        skip_ids = {7, 14, 28, 55, 82}
        
        current_id = 1
        for i in range(1, 100):
            if i in skip_ids:
                current_id += 2 
                continue
                
            account_id = random.choice([101, 102, 103, 104, 105])
            amount = round(random.uniform(10.0, 5000.0), 2)
            
            if i in {12, 35, 77}:
                tx_time = base_time + timedelta(days=i%5, hours=2, minutes=random.randint(0, 59))
            else:
                tx_time = base_time + timedelta(days=i%5, hours=random.randint(9, 20), minutes=random.randint(0, 59))
                
            status = "SUCCESS" if random.random() > 0.05 else "FAILED"
            
            records.append({
                "transaction_id": current_id,
                "account_id": account_id,
                "amount": amount,
                "transaction_timestamp": tx_time,
                "status": status
            })
            
            if i == 20:
                records.append({
                    "transaction_id": current_id + 5000, 
                    "account_id": account_id,
                    "amount": amount,
                    "transaction_timestamp": tx_time,
                    "status": status
                })

            current_id += 1

        for r in records:
            conn.execute(text("""
                INSERT INTO ledger_transactions (transaction_id, account_id, amount, transaction_timestamp, status)
                VALUES (:transaction_id, :account_id, :amount, :transaction_timestamp, :status)
                ON CONFLICT (transaction_id) DO NOTHING;
            """), r)

        print(f"Seeded {len(records)} transactions successfully with test anomalies.")

if __name__ == "__main__":
    seed_database()
