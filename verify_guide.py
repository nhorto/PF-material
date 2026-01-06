"""
READ-ONLY Database Verification - Comparing Guide to Actual Schema
This script ONLY runs SELECT/DESCRIBE/SHOW queries - NO WRITES
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3307)),
    'user': os.getenv('MYSQL_USER', 'admin'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE', 'fabrication'),
    'use_pure': True,
    'auth_plugin': 'mysql_native_password'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 70)
print("VERIFYING POWERFAB GUIDE AGAINST DATABASE (READ-ONLY)")
print("=" * 70)

# 1. Look for Sequence tables
print("\n" + "=" * 70)
print("1. SEARCHING FOR SEQUENCE-RELATED TABLES")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE '%sequence%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 2. Look for Lot tables
print("\n" + "=" * 70)
print("2. SEARCHING FOR LOT-RELATED TABLES")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE '%lot%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 3. What is TimeRecordSubjectID? Look at the actual data
print("\n" + "=" * 70)
print("3. WHAT IS timerecordsubjects? (Sample data)")
print("=" * 70)
cursor.execute("SELECT * FROM timerecordsubjects LIMIT 20")
rows = cursor.fetchall()
cursor.execute("DESCRIBE timerecordsubjects")
cols = [row[0] for row in cursor.fetchall()]
print(f"  Columns: {cols}")
print(f"  Sample rows:")
for row in rows:
    print(f"    {row}")

# 4. What is timerecordsubjectfields?
print("\n" + "=" * 70)
print("4. WHAT IS timerecordsubjectfields?")
print("=" * 70)
cursor.execute("DESCRIBE timerecordsubjectfields")
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25}")
cursor.execute("SELECT * FROM timerecordsubjectfields LIMIT 20")
print("\n  Sample data:")
for row in cursor.fetchall():
    print(f"    {row}")

# 5. Look for production tracking tables (mentioned in guide)
print("\n" + "=" * 70)
print("5. PRODUCTION TRACKING TABLES (Guide mentions these)")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE '%productioncontrol%'")
tables = cursor.fetchall()
print(f"  Found {len(tables)} productioncontrol tables:")
for row in tables[:15]:  # First 15
    print(f"    {row[0]}")
if len(tables) > 15:
    print(f"    ... and {len(tables) - 15} more")

# 6. Look at productioncontrolitemstations (piece-level tracking?)
print("\n" + "=" * 70)
print("6. DESCRIBE productioncontrolitemstations")
print("=" * 70)
cursor.execute("DESCRIBE productioncontrolitemstations")
for row in cursor.fetchall():
    print(f"  {row[0]:40} {str(row[1]):25} Key:{row[3]}")

# 7. Sample from productioncontrolitemstations
print("\n" + "=" * 70)
print("7. SAMPLE: productioncontrolitemstations (5 rows)")
print("=" * 70)
cursor.execute("""
    SELECT * FROM productioncontrolitemstations LIMIT 5
""")
cols = [desc[0] for desc in cursor.description]
print(f"  Columns: {cols[:8]}...")  # First 8 columns
for row in cursor.fetchall():
    print(f"    {row[:8]}...")

# 8. Look for schedule task tables
print("\n" + "=" * 70)
print("8. SCHEDULE TASK TABLES")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE '%scheduletask%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 9. Describe scheduletasks or similar
print("\n" + "=" * 70)
print("9. LOOKING FOR MAIN SCHEDULE TASKS TABLE")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE '%schedule%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 10. Check if timerecords links to sequences indirectly via scheduletasks
print("\n" + "=" * 70)
print("10. CHECKING scheduletasktimerecords (junction table)")
print("=" * 70)
cursor.execute("DESCRIBE scheduletasktimerecords")
for row in cursor.fetchall():
    print(f"  {row[0]:30} {str(row[1]):25}")

cursor.execute("SELECT * FROM scheduletasktimerecords LIMIT 10")
print("\n  Sample data:")
for row in cursor.fetchall():
    print(f"    {row}")

# 11. What tables contain SequenceID column?
print("\n" + "=" * 70)
print("11. WHICH TABLES HAVE A 'Sequence' COLUMN?")
print("=" * 70)
cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND COLUMN_NAME LIKE '%sequence%'
    LIMIT 30
""")
for row in cursor.fetchall():
    print(f"  {row[0]:45} -> {row[1]}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("DONE - All queries were READ-ONLY")
print("=" * 70)
