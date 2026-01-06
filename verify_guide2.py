"""
READ-ONLY Database Verification Part 2
Understanding the TimeRecordSubject system and production control link
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
print("VERIFICATION PART 2 - DEEPER INVESTIGATION (READ-ONLY)")
print("=" * 70)

# 1. How does timerecordsubjectfieldmappings connect things?
print("\n" + "=" * 70)
print("1. DESCRIBE timerecordsubjectfieldmappings")
print("=" * 70)
cursor.execute("DESCRIBE timerecordsubjectfieldmappings")
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25}")

cursor.execute("SELECT * FROM timerecordsubjectfieldmappings LIMIT 15")
print("\n  Sample data:")
for row in cursor.fetchall():
    print(f"    {row}")

# 2. Join timerecords with timerecordsubjectfieldmappings to see actual subjects
print("\n" + "=" * 70)
print("2. TIME RECORDS WITH SUBJECT FIELD VALUES")
print("=" * 70)
cursor.execute("""
    SELECT
        tr.TimeRecordID,
        tr.ProjectID,
        tr.StartDate,
        tr.RegularHours,
        tr.TimeRecordSubjectID,
        tsf.SubjectFieldValue
    FROM timerecords tr
    LEFT JOIN timerecordsubjectfieldmappings tsfm
        ON tr.TimeRecordSubjectID = tsfm.TimeRecordSubjectID
    LEFT JOIN timerecordsubjectfields tsf
        ON tsfm.TimeRecordSubjectFieldID = tsf.TimeRecordSubjectFieldID
    LIMIT 20
""")
print(f"  {'TRec':>5} {'Proj':>5} {'Date':>12} {'Hrs':>8} {'SubjID':>7} | Subject Field Value")
print("  " + "-" * 70)
for row in cursor.fetchall():
    value = str(row[5])[:40] if row[5] else "(none)"
    print(f"  {row[0]:>5} {str(row[1]):>5} {str(row[2]):>12} {str(row[3]):>8} {str(row[4]):>7} | {value}")

# 3. Describe productioncontrolsequences to understand sequences
print("\n" + "=" * 70)
print("3. DESCRIBE productioncontrolsequences")
print("=" * 70)
cursor.execute("DESCRIBE productioncontrolsequences")
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25} Key:{row[3]}")

# 4. Sample productioncontrolsequences
print("\n" + "=" * 70)
print("4. SAMPLE productioncontrolsequences")
print("=" * 70)
cursor.execute("""
    SELECT SequenceID, ProductionControlID, Sequence, Lot
    FROM productioncontrolsequences
    LIMIT 15
""")
print(f"  {'SeqID':>6} {'PCJobID':>8} {'Sequence':>15} {'Lot':>10}")
for row in cursor.fetchall():
    print(f"  {row[0]:>6} {str(row[1]):>8} {str(row[2]):>15} {str(row[3]):>10}")

# 5. What is ProductionControlID? Describe the main productioncontrol table
print("\n" + "=" * 70)
print("5. LOOKING FOR MAIN PRODUCTION CONTROL TABLE")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE 'productioncontrol'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Try productioncontroljobs
print("\n  Checking productioncontroljobs...")
cursor.execute("DESCRIBE productioncontroljobs")
for row in cursor.fetchall():
    print(f"    {row[0]:35} {str(row[1]):25}")

# 6. How does ProductionControlID link to ProjectID in timerecords?
print("\n" + "=" * 70)
print("6. LINKING ProductionControlID TO ProjectID")
print("=" * 70)
cursor.execute("""
    SELECT
        pcj.ProductionControlID,
        pcj.ProjectID,
        p.JobNumber,
        p.JobDescription
    FROM productioncontroljobs pcj
    LEFT JOIN projects p ON pcj.ProjectID = p.ProjectID
    LIMIT 10
""")
print(f"  {'PC_ID':>6} {'ProjID':>8} {'JobNum':>12} {'Description'}")
for row in cursor.fetchall():
    desc = str(row[3])[:35] if row[3] else ""
    print(f"  {row[0]:>6} {str(row[1]):>8} {str(row[2]):>12} {desc}")

# 7. Count of time records
print("\n" + "=" * 70)
print("7. SUMMARY COUNTS")
print("=" * 70)
cursor.execute("SELECT COUNT(*) FROM timerecords")
print(f"  Total time records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM productioncontrolitemstations")
print(f"  Total production tracking records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(DISTINCT EmployeeUserID) FROM timerecords")
print(f"  Unique employees with time: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(DISTINCT ProjectID) FROM timerecords")
print(f"  Projects with time records: {cursor.fetchone()[0]}")

# 8. Time records by station (to verify station is tracked)
print("\n" + "=" * 70)
print("8. TIME RECORDS BY STATION")
print("=" * 70)
cursor.execute("""
    SELECT
        s.StationID,
        s.Description,
        COUNT(*) as Records,
        SUM(tr.RegularHours) as TotalRegHrs,
        SUM(tr.OvertimeHours) as TotalOTHrs
    FROM timerecords tr
    LEFT JOIN stations s ON tr.StationID = s.StationID
    GROUP BY s.StationID, s.Description
    ORDER BY TotalRegHrs DESC
    LIMIT 15
""")
print(f"  {'StaID':>6} {'Station Name':>20} {'Records':>8} {'RegHrs':>12} {'OTHrs':>10}")
for row in cursor.fetchall():
    name = str(row[1])[:20] if row[1] else "(null)"
    print(f"  {str(row[0]):>6} {name:>20} {row[2]:>8} {str(row[3]):>12} {str(row[4]):>10}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("DONE - All queries were READ-ONLY")
print("=" * 70)
