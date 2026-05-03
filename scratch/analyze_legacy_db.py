import sqlite3
import json

def analyze_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        report = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            
            report[table] = {
                'count': count,
                'columns': [c[1] for c in columns]
            }
            
            # Get sample data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 1;")
                report[table]['sample'] = cursor.fetchone()
                
        conn.close()
        return report
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    db_path = r'E:\Gestor_Contas\db.sqlite3'
    result = analyze_db(db_path)
    print(json.dumps(result, indent=2))
