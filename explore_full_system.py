"""
FULL SYSTEM EXPLORATION - READ-ONLY
Exploring: Time Tracking, Production Tracking, Sequences, and Estimating
Goal: Understand how to compare actual hours vs estimated hours
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

print("=" * 75)
print("  FULL SYSTEM EXPLORATION (READ-ONLY)")
print("  Goal: Understand Actual vs Estimated Hours")
print("=" * 75)

# ============================================================================
# PART 1: TIME RECORDS TO SEQUENCES CONNECTION
# ============================================================================
section("PART 1: TIME RECORDS TO SEQUENCES CONNECTION")

subsection("1.1 The Subject Field System - How time connects to sequences")
print("""
The timerecords table does NOT have a direct SequenceID column.
Instead, it uses TimeRecordSubjectID which links to a flexible key-value system:

  timerecords.TimeRecordSubjectID
      |
      v
  timerecordsubjectfieldmappings (junction table)
      |
      v
  timerecordsubjectfields.SubjectFieldValue (contains sequence/piece text)
""")

subsection("1.2 What SubjectFieldID values mean")
cursor.execute("""
    SELECT
        tsfm.SubjectFieldID,
        COUNT(*) as UsageCount,
        COUNT(DISTINCT tsfm.TimeRecordSubjectID) as UniqueSubjects
    FROM timerecordsubjectfieldmappings tsfm
    GROUP BY tsfm.SubjectFieldID
    ORDER BY tsfm.SubjectFieldID
""")
print(f"  {'FieldID':>8} {'UsageCount':>12} {'UniqueSubjects':>15}")
for row in cursor.fetchall():
    print(f"  {row[0]:>8} {row[1]:>12} {row[2]:>15}")

subsection("1.3 Sample SubjectFieldValues by FieldID")
for field_id in [1, 2, 32, 128]:
    cursor.execute("""
        SELECT tsf.SubjectFieldValue
        FROM timerecordsubjectfieldmappings tsfm
        JOIN timerecordsubjectfields tsf ON tsfm.TimeRecordSubjectFieldID = tsf.TimeRecordSubjectFieldID
        WHERE tsfm.SubjectFieldID = %s
        LIMIT 10
    """, (field_id,))
    values = [row[0] for row in cursor.fetchall() if row[0]]
    print(f"  SubjectFieldID {field_id}: {values[:5]}...")

subsection("1.4 Full time record with sequence/piece info")
cursor.execute("""
    SELECT
        tr.TimeRecordID,
        p.JobNumber,
        s.Description as Station,
        u.FirstName,
        tr.StartDate,
        ROUND(tr.RegularHours, 2) as Hours,
        GROUP_CONCAT(tsf.SubjectFieldValue SEPARATOR ' | ') as SubjectInfo
    FROM timerecords tr
    LEFT JOIN projects p ON tr.ProjectID = p.ProjectID
    LEFT JOIN stations s ON tr.StationID = s.StationID
    LEFT JOIN users u ON tr.EmployeeUserID = u.UserID
    LEFT JOIN timerecordsubjectfieldmappings tsfm ON tr.TimeRecordSubjectID = tsfm.TimeRecordSubjectID
    LEFT JOIN timerecordsubjectfields tsf ON tsfm.TimeRecordSubjectFieldID = tsf.TimeRecordSubjectFieldID
    WHERE tr.ProjectID IS NOT NULL
    GROUP BY tr.TimeRecordID, p.JobNumber, s.Description, u.FirstName, tr.StartDate, tr.RegularHours
    LIMIT 15
""")
print(f"  {'ID':>5} {'Job':>8} {'Station':>15} {'Worker':>12} {'Date':>12} {'Hrs':>6} | Subject Info")
print("  " + "-" * 90)
for row in cursor.fetchall():
    subj = str(row[6])[:30] if row[6] else "(none)"
    print(f"  {row[0]:>5} {str(row[1]):>8} {str(row[2] or ''):>15} {str(row[3] or ''):>12} {str(row[4]):>12} {row[5]:>6} | {subj}")

# ============================================================================
# PART 2: PRODUCTION TRACKING IN DEPTH
# ============================================================================
section("PART 2: PRODUCTION TRACKING SYSTEM")

subsection("2.1 Key Production Control Tables")
cursor.execute("SHOW TABLES LIKE 'productioncontrol%'")
tables = [row[0] for row in cursor.fetchall()]
key_tables = [t for t in tables if not t.endswith('log') and not t.startswith('temp')]
print(f"  Found {len(key_tables)} key production control tables (excluding logs/temps)")
for t in sorted(key_tables)[:20]:
    print(f"    {t}")

subsection("2.2 productioncontrolitems - The Bill of Materials")
cursor.execute("DESCRIBE productioncontrolitems")
print("  Key columns in productioncontrolitems:")
for row in cursor.fetchall():
    if row[3]:  # Has a key
        print(f"    {row[0]:35} {str(row[1]):20} Key:{row[3]}")
    elif row[0] in ['ProductionControlItemID', 'ProductionControlID', 'MainMark', 'PieceMark', 'Description', 'Quantity', 'Weight', 'SequenceID']:
        print(f"    {row[0]:35} {str(row[1]):20}")

subsection("2.3 Sample Bill of Materials Items")
cursor.execute("""
    SELECT
        pci.ProductionControlItemID,
        pci.ProductionControlID,
        pci.MainMark,
        pci.PieceMark,
        pci.Description,
        pci.Quantity,
        pci.SequenceID
    FROM productioncontrolitems pci
    LIMIT 10
""")
print(f"  {'ItemID':>8} {'JobID':>6} {'Main':>10} {'Piece':>12} {'Qty':>4} {'SeqID':>6} Description")
for row in cursor.fetchall():
    desc = str(row[4])[:25] if row[4] else ""
    main = str(row[2]).replace('\x01', '')[:10] if row[2] else ""
    piece = str(row[3]).replace('\x01', '')[:12] if row[3] else ""
    print(f"  {row[0]:>8} {str(row[1]):>6} {main:>10} {piece:>12} {str(row[5]):>4} {str(row[6]):>6} {desc}")

subsection("2.4 productioncontrolitemstations - Piece-Level Completion")
cursor.execute("DESCRIBE productioncontrolitemstations")
print("  Columns in productioncontrolitemstations:")
for row in cursor.fetchall():
    print(f"    {row[0]:40} {str(row[1]):20}")

subsection("2.5 Sample Production Tracking Records")
cursor.execute("""
    SELECT
        pcis.ProductionControlID,
        pcis.MainMark,
        pcis.PieceMark,
        pcis.SequenceID,
        s.Description as Station,
        pcis.Quantity,
        pcis.DateCompleted,
        pcis.Hours,
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
    hrs = str(row[7])[:8] if row[7] else ""
    print(f"  {str(row[0]):>6} {main:>12} {piece:>12} {str(row[3]):>6} {str(row[4] or ''):>15} {str(row[5]):>4} {str(row[6]):>12} {hrs:>8} {str(row[8] or ''):>10}")

subsection("2.6 Sequences with Lot Numbers")
cursor.execute("""
    SELECT
        pcs.SequenceID,
        pcs.ProductionControlID,
        pcs.Description as SequenceName,
        pcs.LotNumber,
        COUNT(pci.ProductionControlItemID) as ItemCount
    FROM productioncontrolsequences pcs
    LEFT JOIN productioncontrolitems pci ON pcs.SequenceID = pci.SequenceID
    GROUP BY pcs.SequenceID, pcs.ProductionControlID, pcs.Description, pcs.LotNumber
    HAVING ItemCount > 0
    LIMIT 15
""")
print(f"  {'SeqID':>6} {'JobID':>6} {'Sequence':>15} {'Lot':>10} {'Items':>6}")
for row in cursor.fetchall():
    print(f"  {row[0]:>6} {str(row[1]):>6} {str(row[2] or ''):>15} {str(row[3] or ''):>10} {row[4]:>6}")

# ============================================================================
# PART 3: ESTIMATING TABLES - FOR ESTIMATE VS ACTUAL
# ============================================================================
section("PART 3: ESTIMATING SYSTEM (For Estimate vs Actual)")

subsection("3.1 Finding Estimating Tables")
cursor.execute("SHOW TABLES LIKE '%estimat%'")
tables = [row[0] for row in cursor.fetchall()]
key_tables = [t for t in tables if not t.endswith('log') and not t.startswith('temp')]
print(f"  Found {len(key_tables)} estimating-related tables:")
for t in sorted(key_tables)[:25]:
    print(f"    {t}")

subsection("3.2 Looking for Labor Estimates")
cursor.execute("SHOW TABLES LIKE '%labor%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

subsection("3.3 Describe estimateitems (if exists)")
try:
    cursor.execute("DESCRIBE estimateitems")
    print("  Key columns in estimateitems:")
    for row in cursor.fetchall():
        if 'labor' in row[0].lower() or 'hour' in row[0].lower() or 'cost' in row[0].lower() or row[3]:
            print(f"    {row[0]:40} {str(row[1]):20}")
except:
    print("  Table estimateitems not found or not accessible")

subsection("3.4 Describe estimates table")
try:
    cursor.execute("DESCRIBE estimates")
    print("  Key columns in estimates:")
    for row in cursor.fetchall():
        if row[3] or 'labor' in row[0].lower() or 'hour' in row[0].lower() or 'job' in row[0].lower():
            print(f"    {row[0]:40} {str(row[1]):20} Key:{row[3]}")
except:
    print("  Table estimates not found")

subsection("3.5 Looking for estimate-to-job linkage")
cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND (COLUMN_NAME LIKE '%EstimateID%' OR COLUMN_NAME LIKE '%EstimatingJob%')
    AND TABLE_NAME NOT LIKE '%log'
    LIMIT 30
""")
print("  Tables with EstimateID or EstimatingJob columns:")
for row in cursor.fetchall():
    print(f"    {row[0]:45} -> {row[1]}")

subsection("3.6 Labor Groups (mentioned in guide)")
cursor.execute("SHOW TABLES LIKE '%laborgroup%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

try:
    cursor.execute("DESCRIBE laborgroups")
    print("\n  Columns in laborgroups:")
    for row in cursor.fetchall():
        print(f"    {row[0]:35} {str(row[1]):20}")
except:
    print("  laborgroups table not found")

subsection("3.7 Sample from laborgroups")
try:
    cursor.execute("SELECT * FROM laborgroups LIMIT 10")
    cols = [desc[0] for desc in cursor.description]
    print(f"  Columns: {cols}")
    for row in cursor.fetchall():
        print(f"    {row}")
except Exception as e:
    print(f"  Error: {e}")

subsection("3.8 Station to Labor Group mapping")
cursor.execute("DESCRIBE stations")
print("  Looking for LaborGroupID in stations table:")
for row in cursor.fetchall():
    if 'labor' in row[0].lower() or 'group' in row[0].lower():
        print(f"    {row[0]:35} {str(row[1]):20}")

# Check stationlaborgroups
try:
    cursor.execute("DESCRIBE stationlaborgroups")
    print("\n  stationlaborgroups table exists:")
    for row in cursor.fetchall():
        print(f"    {row[0]:35} {str(row[1]):20}")

    cursor.execute("SELECT * FROM stationlaborgroups LIMIT 10")
    print("\n  Sample data:")
    for row in cursor.fetchall():
        print(f"    {row}")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================================
# PART 4: CONNECTING ESTIMATES TO ACTUALS
# ============================================================================
section("PART 4: THE ESTIMATE VS ACTUAL CONNECTION")

subsection("4.1 How Projects link to Estimates")
cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND TABLE_NAME = 'projects'
    AND (COLUMN_NAME LIKE '%estim%' OR COLUMN_NAME LIKE '%job%')
""")
print("  Estimate-related columns in projects table:")
for row in cursor.fetchall():
    print(f"    {row[0]}")

subsection("4.2 Check productioncontroljobs for estimate link")
cursor.execute("DESCRIBE productioncontroljobs")
print("  Columns in productioncontroljobs:")
for row in cursor.fetchall():
    print(f"    {row[0]:40} {str(row[1]):20}")

subsection("4.3 Looking for EstimatingJobID connections")
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

subsection("4.4 Check if estimates table has labor hours")
try:
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'fabrication'
        AND TABLE_NAME = 'estimates'
    """)
    print("  All columns in estimates:")
    for row in cursor.fetchall():
        print(f"    {row[0]}")
except:
    print("  Could not read estimates columns")

subsection("4.5 Look for estimate labor/hours tables")
cursor.execute("SHOW TABLES LIKE '%estimatelabor%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.execute("SHOW TABLES LIKE '%estimatehour%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.execute("SHOW TABLES LIKE '%jobcost%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
conn.close()

print("\n" + "=" * 75)
print("  EXPLORATION COMPLETE (ALL READ-ONLY)")
print("=" * 75)
