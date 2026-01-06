"""
READ-ONLY Database Verification Part 3 - Final pieces
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
print("VERIFICATION PART 3 - FINAL PIECES (READ-ONLY)")
print("=" * 70)

# 1. Sample productioncontrolsequences (fixed columns)
print("\n" + "=" * 70)
print("1. SAMPLE productioncontrolsequences (Sequence + Lot)")
print("=" * 70)
cursor.execute("""
    SELECT SequenceID, ProductionControlID, Description, LotNumber
    FROM productioncontrolsequences
    LIMIT 15
""")
print(f"  {'SeqID':>6} {'PCJobID':>8} {'Description':>15} {'LotNumber':>15}")
for row in cursor.fetchall():
    lot = str(row[3]) if row[3] else "(none)"
    print(f"  {row[0]:>6} {str(row[1]):>8} {str(row[2]):>15} {lot:>15}")

# 2. Link production control to projects
print("\n" + "=" * 70)
print("2. ProductionControlID TO ProjectID LINK")
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
print(f"  {'PC_ID':>6} {'ProjID':>8} {'JobNum':>12} Description")
for row in cursor.fetchall():
    desc = str(row[3])[:35] if row[3] else ""
    print(f"  {row[0]:>6} {str(row[1]):>8} {str(row[2]):>12} {desc}")

# 3. Summary counts
print("\n" + "=" * 70)
print("3. SUMMARY COUNTS")
print("=" * 70)
cursor.execute("SELECT COUNT(*) FROM timerecords")
print(f"  Total time records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM productioncontrolitemstations")
print(f"  Total production tracking records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(DISTINCT EmployeeUserID) FROM timerecords")
print(f"  Unique employees with time: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(DISTINCT ProjectID) FROM timerecords")
print(f"  Projects with time records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM productioncontrolsequences")
print(f"  Total sequences defined: {cursor.fetchone()[0]}")

# 4. Time records by station
print("\n" + "=" * 70)
print("4. TIME RECORDS BY STATION (Top 15)")
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
    reg = float(row[3]) if row[3] else 0
    ot = float(row[4]) if row[4] else 0
    print(f"  {str(row[0]):>6} {name:>20} {row[2]:>8} {reg:>12.1f} {ot:>10.1f}")

# 5. Time records by project
print("\n" + "=" * 70)
print("5. TIME RECORDS BY PROJECT (Top 15)")
print("=" * 70)
cursor.execute("""
    SELECT
        p.ProjectID,
        p.JobNumber,
        p.JobDescription,
        COUNT(*) as Records,
        SUM(tr.RegularHours) as TotalRegHrs,
        SUM(tr.OvertimeHours) as TotalOTHrs
    FROM timerecords tr
    LEFT JOIN projects p ON tr.ProjectID = p.ProjectID
    GROUP BY p.ProjectID, p.JobNumber, p.JobDescription
    ORDER BY TotalRegHrs DESC
    LIMIT 15
""")
print(f"  {'ProjID':>6} {'Job#':>10} {'Description':>25} {'Recs':>6} {'RegHrs':>10} {'OTHrs':>8}")
for row in cursor.fetchall():
    desc = str(row[2])[:25] if row[2] else ""
    reg = float(row[4]) if row[4] else 0
    ot = float(row[5]) if row[5] else 0
    print(f"  {str(row[0]):>6} {str(row[1]):>10} {desc:>25} {row[3]:>6} {reg:>10.1f} {ot:>8.1f}")

# 6. Time records by employee
print("\n" + "=" * 70)
print("6. TIME RECORDS BY EMPLOYEE (Top 15)")
print("=" * 70)
cursor.execute("""
    SELECT
        u.UserID,
        u.FirstName,
        u.LastName,
        COUNT(*) as Records,
        SUM(tr.RegularHours) as TotalRegHrs,
        SUM(tr.OvertimeHours) as TotalOTHrs
    FROM timerecords tr
    LEFT JOIN users u ON tr.EmployeeUserID = u.UserID
    GROUP BY u.UserID, u.FirstName, u.LastName
    ORDER BY TotalRegHrs DESC
    LIMIT 15
""")
print(f"  {'UserID':>6} {'Name':>25} {'Recs':>6} {'RegHrs':>10} {'OTHrs':>8}")
for row in cursor.fetchall():
    name = f"{row[1] or ''} {row[2] or ''}"[:25]
    reg = float(row[4]) if row[4] else 0
    ot = float(row[5]) if row[5] else 0
    print(f"  {str(row[0]):>6} {name:>25} {row[3]:>6} {reg:>10.1f} {ot:>8.1f}")

# 7. Check SubjectFieldID meanings
print("\n" + "=" * 70)
print("7. WHAT DO SubjectFieldID VALUES MEAN?")
print("=" * 70)
cursor.execute("""
    SELECT DISTINCT SubjectFieldID
    FROM timerecordsubjectfieldmappings
    ORDER BY SubjectFieldID
""")
print("  Distinct SubjectFieldID values used:")
for row in cursor.fetchall():
    print(f"    {row[0]}")

# 8. Look for a subjectfield definition table
print("\n" + "=" * 70)
print("8. SEARCHING FOR SUBJECT FIELD DEFINITIONS")
print("=" * 70)
cursor.execute("SHOW TABLES LIKE '%subjectfield%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Maybe it's in variables tables?
cursor.execute("SHOW TABLES LIKE '%variablestimerecord%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("DONE - All queries were READ-ONLY")
print("=" * 70)
