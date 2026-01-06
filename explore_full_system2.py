"""
FULL SYSTEM EXPLORATION PART 2 - READ-ONLY
Continuing from where Part 1 left off
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

def section(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def subsection(title):
    print(f"\n--- {title} ---")

# ============================================================================
# PART 2: PRODUCTION TRACKING CONTINUED
# ============================================================================
section("PART 2: PRODUCTION TRACKING SYSTEM (CONTINUED)")

subsection("2.3 Sample Bill of Materials Items")
cursor.execute("""
    SELECT
        pci.ProductionControlItemID,
        pci.ProductionControlID,
        pci.MainMark,
        pci.PieceMark,
        pci.Quantity,
        pci.Weight
    FROM productioncontrolitems pci
    LIMIT 10
""")
print(f"  {'ItemID':>10} {'JobID':>6} {'MainMark':>15} {'PieceMark':>15} {'Qty':>5} {'Weight':>10}")
for row in cursor.fetchall():
    main = str(row[2]).replace('\x01', '')[:15] if row[2] else ""
    piece = str(row[3]).replace('\x01', '')[:15] if row[3] else ""
    wt = str(round(float(row[5]), 1)) if row[5] else ""
    print(f"  {row[0]:>10} {str(row[1]):>6} {main:>15} {piece:>15} {str(row[4]):>5} {wt:>10}")

subsection("2.4 productioncontrolitemstations - Piece Completion Tracking")
cursor.execute("""
    SELECT
        pcis.ProductionControlID,
        pcis.MainMark,
        pcis.PieceMark,
        pcis.SequenceID,
        s.Description as Station,
        pcis.Quantity,
        pcis.DateCompleted,
        ROUND(pcis.Hours, 2) as Hours,
        u.FirstName as CompletedBy
    FROM productioncontrolitemstations pcis
    LEFT JOIN stations s ON pcis.StationID = s.StationID
    LEFT JOIN users u ON pcis.UserID = u.UserID
    WHERE pcis.DateCompleted IS NOT NULL
    LIMIT 15
""")
print(f"  {'JobID':>6} {'Main':>12} {'Piece':>12} {'SeqID':>6} {'Station':>15} {'Qty':>4} {'Date':>12} {'Hrs':>8} {'By':>10}")
for row in cursor.fetchall():
    main = str(row[1]).replace('\x01', '')[:12] if row[1] else ""
    piece = str(row[2]).replace('\x01', '')[:12] if row[2] else ""
    hrs = str(row[7]) if row[7] else ""
    print(f"  {str(row[0]):>6} {main:>12} {piece:>12} {str(row[3]):>6} {str(row[4] or ''):>15} {str(row[5]):>4} {str(row[6]):>12} {hrs:>8} {str(row[8] or ''):>10}")

subsection("2.5 Sequences with Lot Numbers")
cursor.execute("""
    SELECT
        pcs.SequenceID,
        pcs.ProductionControlID,
        pcs.Description as SequenceName,
        pcs.LotNumber
    FROM productioncontrolsequences pcs
    WHERE pcs.Description IS NOT NULL OR pcs.LotNumber IS NOT NULL
    LIMIT 15
""")
print(f"  {'SeqID':>8} {'JobID':>6} {'SequenceName':>20} {'LotNumber':>15}")
for row in cursor.fetchall():
    print(f"  {row[0]:>8} {str(row[1]):>6} {str(row[2] or ''):>20} {str(row[3] or ''):>15}")

# ============================================================================
# PART 3: ESTIMATING SYSTEM
# ============================================================================
section("PART 3: ESTIMATING SYSTEM (For Estimate vs Actual)")

subsection("3.1 Finding Estimating Tables")
cursor.execute("SHOW TABLES LIKE '%estimat%'")
tables = [row[0] for row in cursor.fetchall()]
key_tables = [t for t in tables if not t.endswith('log') and not t.startswith('temp')]
print(f"  Found {len(key_tables)} estimating tables (excluding logs/temps):")
for t in sorted(key_tables)[:20]:
    print(f"    {t}")

subsection("3.2 Labor-related Tables")
cursor.execute("SHOW TABLES LIKE '%labor%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

subsection("3.3 Describe estimates table")
try:
    cursor.execute("DESCRIBE estimates")
    print("  Columns in estimates:")
    for row in cursor.fetchall():
        print(f"    {row[0]:40} {str(row[1]):25}")
except Exception as e:
    print(f"  Error: {e}")

subsection("3.4 Looking for estimated hours in estimateitems")
try:
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'fabrication'
        AND TABLE_NAME = 'estimateitems'
        AND (COLUMN_NAME LIKE '%hour%' OR COLUMN_NAME LIKE '%labor%' OR COLUMN_NAME LIKE '%cost%' OR COLUMN_NAME LIKE '%time%')
    """)
    print("  Hour/Labor/Cost columns in estimateitems:")
    for row in cursor.fetchall():
        print(f"    {row[0]}")
except Exception as e:
    print(f"  Error: {e}")

subsection("3.5 Labor Groups")
try:
    cursor.execute("DESCRIBE laborgroups")
    print("  Columns in laborgroups:")
    for row in cursor.fetchall():
        print(f"    {row[0]:35} {str(row[1]):25}")

    cursor.execute("SELECT LaborGroupID, Description FROM laborgroups LIMIT 10")
    print("\n  Sample labor groups:")
    for row in cursor.fetchall():
        print(f"    ID:{row[0]:>4} | {row[1]}")
except Exception as e:
    print(f"  Error: {e}")

subsection("3.6 Station to Labor Group Mapping")
try:
    cursor.execute("DESCRIBE stationlaborgroups")
    print("  Columns in stationlaborgroups:")
    for row in cursor.fetchall():
        print(f"    {row[0]:35} {str(row[1]):25}")

    cursor.execute("""
        SELECT slg.StationID, s.Description as Station, slg.LaborGroupID, lg.Description as LaborGroup
        FROM stationlaborgroups slg
        LEFT JOIN stations s ON slg.StationID = s.StationID
        LEFT JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
        LIMIT 15
    """)
    print("\n  Station -> Labor Group mappings:")
    for row in cursor.fetchall():
        print(f"    Station:{str(row[1] or ''):>20} -> LaborGroup:{str(row[3] or '')}")
except Exception as e:
    print(f"  Error: {e}")

subsection("3.7 How Projects Link to Estimates")
cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND TABLE_NAME = 'projects'
""")
cols = [row[0] for row in cursor.fetchall()]
print("  All columns in projects table:")
for col in cols:
    print(f"    {col}")

subsection("3.8 EstimatingJobID connections")
cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND COLUMN_NAME = 'EstimatingJobID'
    AND TABLE_NAME NOT LIKE '%log'
    LIMIT 20
""")
print("  Tables with EstimatingJobID:")
for row in cursor.fetchall():
    print(f"    {row[0]}")

# ============================================================================
# PART 4: THE ESTIMATE TO ACTUAL PATH
# ============================================================================
section("PART 4: CONNECTING ESTIMATES TO ACTUALS")

subsection("4.1 Check productioncontroljobs for estimate link")
cursor.execute("DESCRIBE productioncontroljobs")
print("  Columns in productioncontroljobs:")
for row in cursor.fetchall():
    print(f"    {row[0]:40} {str(row[1]):25}")

subsection("4.2 Sample productioncontroljobs with EstimatingJobID")
cursor.execute("""
    SELECT ProductionControlID, ProjectID, EstimatingJobID
    FROM productioncontroljobs
    WHERE EstimatingJobID IS NOT NULL
    LIMIT 10
""")
print(f"  {'PCJobID':>8} {'ProjectID':>10} {'EstJobID':>10}")
for row in cursor.fetchall():
    print(f"  {row[0]:>8} {str(row[1]):>10} {str(row[2]):>10}")

subsection("4.3 Estimating Jobs table")
try:
    cursor.execute("SHOW TABLES LIKE '%estimatingjob%'")
    for row in cursor.fetchall():
        print(f"  {row[0]}")

    cursor.execute("SHOW TABLES LIKE 'estimatejob%'")
    for row in cursor.fetchall():
        print(f"  {row[0]}")
except Exception as e:
    print(f"  Error: {e}")

subsection("4.4 Looking for estimate item labor hours")
try:
    cursor.execute("""
        SELECT
            ei.EstimateItemID,
            ei.EstimateID,
            ei.LaborHours,
            ei.LaborCost
        FROM estimateitems ei
        WHERE ei.LaborHours > 0
        LIMIT 10
    """)
    print("  Sample estimate items with labor hours:")
    for row in cursor.fetchall():
        print(f"    ItemID:{row[0]} EstID:{row[1]} Hours:{row[2]} Cost:{row[3]}")
except Exception as e:
    print(f"  Checking for different column names...")
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'fabrication'
        AND TABLE_NAME = 'estimateitems'
    """)
    print("  All columns in estimateitems:")
    for row in cursor.fetchall():
        print(f"    {row[0]}")

subsection("4.5 Estimate labor by labor group")
cursor.execute("SHOW TABLES LIKE '%estimatelabor%'")
tables = cursor.fetchall()
if tables:
    for t in tables:
        print(f"  Found: {t[0]}")
        cursor.execute(f"DESCRIBE {t[0]}")
        print(f"  Columns:")
        for row in cursor.fetchall():
            print(f"    {row[0]:35} {str(row[1]):25}")
else:
    print("  No estimatelabor tables found")

subsection("4.6 Looking for estimate job cost summary")
cursor.execute("SHOW TABLES LIKE '%jobcost%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.execute("SHOW TABLES LIKE '%estimatejobcost%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

subsection("4.7 Estimate item labor details")
cursor.execute("SHOW TABLES LIKE 'estimateitemlabor%'")
tables = cursor.fetchall()
if tables:
    for t in tables:
        print(f"  Found: {t[0]}")
        cursor.execute(f"DESCRIBE {t[0]}")
        for row in cursor.fetchall():
            print(f"    {row[0]:35} {str(row[1]):25}")

cursor.close()
conn.close()

print("\n" + "=" * 75)
print("  EXPLORATION COMPLETE (ALL READ-ONLY)")
print("=" * 75)
