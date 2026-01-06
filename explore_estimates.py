"""
ESTIMATE EXPLORATION - READ-ONLY
Understanding the estimate side for actual vs estimated comparison
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

section("ESTIMATE SYSTEM EXPLORATION")

subsection("1. productioncontroljobs - The Link Between Production and Estimates")
cursor.execute("""
    SELECT
        pcj.ProductionControlID,
        pcj.ProjectID,
        pcj.EstimateID,
        ROUND(pcj.TotalManHours, 2) as EstimatedManHours,
        ROUND(pcj.TotalWeight, 2) as TotalWeight
    FROM productioncontroljobs pcj
    WHERE pcj.EstimateID IS NOT NULL
    LIMIT 10
""")
print(f"  {'PCJobID':>8} {'ProjID':>8} {'EstID':>8} {'EstManHrs':>12} {'TotalWt':>12}")
for row in cursor.fetchall():
    print(f"  {row[0]:>8} {str(row[1] or ''):>8} {str(row[2] or ''):>8} {str(row[3] or ''):>12} {str(row[4] or ''):>12}")

subsection("2. Describe estimates table")
cursor.execute("DESCRIBE estimates")
print("  Key columns in estimates:")
for row in cursor.fetchall():
    if 'hour' in row[0].lower() or 'labor' in row[0].lower() or 'cost' in row[0].lower() or row[3]:
        print(f"    {row[0]:40} {str(row[1]):25}")

subsection("3. Sample estimates data")
cursor.execute("""
    SELECT
        EstimateID,
        JobNumber,
        Description
    FROM estimates
    LIMIT 10
""")
print(f"  {'EstID':>8} {'JobNumber':>12} Description")
for row in cursor.fetchall():
    desc = str(row[2])[:40] if row[2] else ""
    print(f"  {row[0]:>8} {str(row[1] or ''):>12} {desc}")

subsection("4. Describe estimateitems")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND TABLE_NAME = 'estimateitems'
""")
print("  All columns in estimateitems:")
for row in cursor.fetchall():
    print(f"    {row[0]:40} {row[1]}")

subsection("5. Sample estimateitems with labor")
cursor.execute("""
    SELECT
        ei.EstimateItemID,
        ei.EstimateID,
        ei.MainMark,
        ei.PieceMark,
        ei.Quantity,
        ei.TotalLabor
    FROM estimateitems ei
    WHERE ei.TotalLabor IS NOT NULL AND ei.TotalLabor > 0
    LIMIT 15
""")
print(f"  {'ItemID':>10} {'EstID':>8} {'Main':>12} {'Piece':>12} {'Qty':>5} {'TotalLabor':>12}")
for row in cursor.fetchall():
    main = str(row[2])[:12] if row[2] else ""
    piece = str(row[3])[:12] if row[3] else ""
    print(f"  {row[0]:>10} {str(row[1]):>8} {main:>12} {piece:>12} {str(row[4]):>5} {str(row[5]):>12}")

subsection("6. Labor Groups - Categories of Labor")
cursor.execute("SELECT LaborGroupID, Description FROM laborgroups LIMIT 15")
print("  Labor Groups defined:")
for row in cursor.fetchall():
    print(f"    ID:{row[0]:>3} | {row[1]}")

subsection("7. Station to Labor Group Mapping")
cursor.execute("""
    SELECT
        s.StationID,
        s.Description as Station,
        lg.LaborGroupID,
        lg.Description as LaborGroup
    FROM stationlaborgroups slg
    JOIN stations s ON slg.StationID = s.StationID
    JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
    LIMIT 15
""")
print("  How Stations map to Labor Groups (for estimate comparison):")
print(f"    {'Station':>20} -> {'Labor Group'}")
for row in cursor.fetchall():
    print(f"    {str(row[1]):>20} -> {row[3]}")

subsection("8. Actual Hours from timerecords by Project")
cursor.execute("""
    SELECT
        p.ProjectID,
        p.JobNumber,
        COUNT(*) as TimeEntries,
        ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours), 2) as ActualHours
    FROM timerecords tr
    JOIN projects p ON tr.ProjectID = p.ProjectID
    GROUP BY p.ProjectID, p.JobNumber
    ORDER BY ActualHours DESC
    LIMIT 10
""")
print("  Actual Hours by Project (from timerecords):")
print(f"    {'ProjID':>8} {'JobNum':>12} {'Entries':>8} {'ActualHrs':>12}")
for row in cursor.fetchall():
    print(f"    {row[0]:>8} {str(row[1]):>12} {row[2]:>8} {row[3]:>12}")

subsection("9. Estimated Hours from productioncontroljobs")
cursor.execute("""
    SELECT
        pcj.ProductionControlID,
        pcj.ProjectID,
        pcj.EstimateID,
        ROUND(pcj.TotalManHours, 2) as EstimatedHours
    FROM productioncontroljobs pcj
    WHERE pcj.TotalManHours IS NOT NULL AND pcj.TotalManHours > 0
    ORDER BY pcj.TotalManHours DESC
    LIMIT 10
""")
print("  Estimated Hours by Production Control Job:")
print(f"    {'PCJobID':>8} {'ProjID':>10} {'EstID':>8} {'EstHours':>12}")
for row in cursor.fetchall():
    print(f"    {row[0]:>8} {str(row[1] or ''):>10} {str(row[2] or ''):>8} {row[3]:>12}")

subsection("10. JOINING Estimated vs Actual at Job Level")
cursor.execute("""
    SELECT
        p.JobNumber,
        p.JobDescription,
        pcj.ProductionControlID,
        ROUND(pcj.TotalManHours, 2) as EstimatedHours,
        ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours), 2) as ActualHours,
        ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours, 2) as Variance
    FROM projects p
    JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
    JOIN timerecords tr ON p.ProjectID = tr.ProjectID
    WHERE pcj.TotalManHours IS NOT NULL AND pcj.TotalManHours > 0
    GROUP BY p.JobNumber, p.JobDescription, pcj.ProductionControlID, pcj.TotalManHours
    ORDER BY ABS(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours) DESC
    LIMIT 15
""")
print("  ESTIMATED vs ACTUAL Hours by Job:")
print(f"    {'Job#':>10} {'Description':>25} {'Estimated':>12} {'Actual':>12} {'Variance':>12}")
for row in cursor.fetchall():
    desc = str(row[1])[:25] if row[1] else ""
    print(f"    {str(row[0]):>10} {desc:>25} {row[3]:>12} {row[4]:>12} {row[5]:>12}")

subsection("11. Production Tracking Hours (piece-level)")
cursor.execute("""
    SELECT
        pcis.ProductionControlID,
        pcis.MainMark,
        s.Description as Station,
        SUM(pcis.Quantity) as TotalPieces,
        ROUND(SUM(pcis.Hours), 2) as TotalHours
    FROM productioncontrolitemstations pcis
    JOIN stations s ON pcis.StationID = s.StationID
    WHERE pcis.Hours IS NOT NULL AND pcis.Hours > 0
    GROUP BY pcis.ProductionControlID, pcis.MainMark, s.Description
    LIMIT 15
""")
print("  Hours tracked at piece level (productioncontrolitemstations):")
print(f"    {'JobID':>6} {'MainMark':>15} {'Station':>15} {'Pieces':>8} {'Hours':>10}")
for row in cursor.fetchall():
    main = str(row[1]).replace('\x01', '')[:15] if row[1] else ""
    print(f"    {str(row[0]):>6} {main:>15} {str(row[2]):>15} {row[3]:>8} {str(row[4]):>10}")

cursor.close()
conn.close()

print("\n" + "=" * 75)
print("  EXPLORATION COMPLETE (ALL READ-ONLY)")
print("=" * 75)
