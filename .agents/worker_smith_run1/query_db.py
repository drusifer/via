import sqlite3
import json

db_path = "/home/drusifer/Projects/via/.via/index.db"

def run_query(query, params=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Query 1: Scenario 3 symbols in via/core/
q1 = "SELECT symbol_name, qualified_name, file_path, symbol_type FROM symbols WHERE file_path LIKE '%via/core%'"
res1 = run_query(q1)

# Query 2: Let's also get a list of distinct file paths from the symbols table to see how they are formatted.
q2 = "SELECT DISTINCT file_path FROM symbols LIMIT 10"
res2 = run_query(q2)

# Query 3: Let's see all symbols matching '*sqlite3*'
q3 = "SELECT * FROM symbols WHERE symbol_name LIKE '%sqlite3%' OR qualified_name LIKE '%sqlite3%'"
res3 = run_query(q3)

# Query 4: Let's see relationships involving sqlite3 symbols (either from_symbol or to_symbol)
q4 = """
SELECT 
    sr.id,
    sr.reference_type,
    sr.line_number,
    fs.symbol_name as from_name,
    fs.qualified_name as from_qual,
    fs.symbol_type as from_type,
    ts.symbol_name as to_name,
    ts.qualified_name as to_qual,
    ts.symbol_type as to_type
FROM symbol_references sr
JOIN symbols fs ON sr.from_symbol_id = fs.id
JOIN symbols ts ON sr.to_symbol_id = ts.id
WHERE fs.symbol_name LIKE '%sqlite3%' 
   OR fs.qualified_name LIKE '%sqlite3%'
   OR ts.symbol_name LIKE '%sqlite3%'
   OR ts.qualified_name LIKE '%sqlite3%'
"""
res4 = run_query(q4)

# Query 5: Scenario 14 - imports matching '*executor*' or references to 'executor'
q5 = "SELECT * FROM symbols WHERE symbol_name LIKE '%executor%' OR qualified_name LIKE '%executor%'"
res5 = run_query(q5)

q6 = """
SELECT 
    sr.id,
    sr.reference_type,
    sr.line_number,
    fs.symbol_name as from_name,
    fs.qualified_name as from_qual,
    fs.symbol_type as from_type,
    ts.symbol_name as to_name,
    ts.qualified_name as to_qual,
    ts.symbol_type as to_type
FROM symbol_references sr
JOIN symbols fs ON sr.from_symbol_id = fs.id
JOIN symbols ts ON sr.to_symbol_id = ts.id
WHERE fs.symbol_name LIKE '%executor%' 
   OR fs.qualified_name LIKE '%executor%'
   OR ts.symbol_name LIKE '%executor%'
   OR ts.qualified_name LIKE '%executor%'
"""
res6 = run_query(q6)

output = {
    "symbols_in_via_core": res1,
    "distinct_file_paths": res2,
    "sqlite3_symbols": res3,
    "sqlite3_relationships": res4,
    "executor_symbols": res5,
    "executor_relationships": res6
}

with open("/home/drusifer/Projects/via/.agents/worker_smith_run1/db_results.json", "w") as f:
    json.dump(output, f, indent=2)

print("DB queries run successfully!")
