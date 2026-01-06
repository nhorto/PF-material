"""
ESTIMATE EXPLORATION PART 2 - READ-ONLY
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

section("ESTIMATE EXPLORATION PART 2")

subsection("1. All columns in estimates table")
cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND TABLE_NAME = 'estimates'
""")
print("  Columns in estimates:")
for row in cursor.fetchall():
    print(f"    {row[0]}")

subsection("2. Sample from estimates")
cursor.execute("""
    SELECT EstimateID, ROUND(TotalManHours, 2) as TotalManHours
    FROM estimates
    WHERE TotalManHours IS NOT NULL AND TotalManHours > 0
    LIMIT 10
""")
print(f"  {'EstID':>8} {'TotalManHours':>15}")
for row in cursor.fetchall():
    print(f"  {row[0]:>8} {str(row[1]):>15}")

subsection("3. estimateitems - Piece level estimates")
cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'fabrication'
    AND TABLE_NAME = 'estimateitems'
    ORDER BY COLUMN_NAME
""")
print("  All columns in estimateitems:")
cols = [row[0] for row in cursor.fetchall()]
# Show labor-related columns
labor_cols = [c for c in cols if 'labor' in c.lower() or 'hour' in c.lower()]
print(f"  Labor-related columns: {labor_cols}")

subsection("4. Sample estimateitems")
cursor.execute("""
    SELECT
        EstimateItemID,
        EstimateID,
        MainMark,
        PieceMark,
        Quantity,
        TotalLabor
    FROM estimateitems
    WHERE TotalLabor > 0
    LIMIT 15
""")
print(f"  {'ItemID':>10} {'EstID':>8} {'Main':>12} {'Piece':>12} {'Qty':>5} {'Labor':>12}")
for row in cursor.fetchall():
    main = str(row[2])[:12] if row[2] else ""
    piece = str(row[3])[:12] if row[3] else ""
    print(f"  {row[0]:>10} {str(row[1]):>8} {main:>12} {piece:>12} {str(row[4]):>5} {str(row[5]):>12}")

subsection("5. Labor Groups")
cursor.execute("SELECT LaborGroupID, Description FROM laborgroups LIMIT 20")
print("  Labor Groups:")
for row in cursor.fetchall():
    print(f"    ID:{row[0]:>3} | {row[1]}")

subsection("6. Station to Labor Group Mapping")
cursor.execute("""
    SELECT
        s.StationID,
        s.Description as Station,
        lg.LaborGroupID,
        lg.Description as LaborGroup
    FROM stationlaborgroups slg
    JOIN stations s ON slg.StationID = s.StationID
    JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
""")
print("  Station -> Labor Group mappings:")
for row in cursor.fetchall():
    print(f"    {str(row[1]):>20} -> {row[3]}")

subsection("7. ACTUAL HOURS by Project (from timerecords)")
cursor.execute("""
    SELECT
        tr.ProjectID,
        p.JobNumber,
        p.JobDescription,
        ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours), 2) as ActualHours
    FROM timerecords tr
    LEFT JOIN projects p ON tr.ProjectID = p.ProjectID
    WHERE tr.ProjectID IS NOT NULL
    GROUP BY tr.ProjectID, p.JobNumber, p.JobDescription
    ORDER BY ActualHours DESC
    LIMIT 10
""")
print("  Actual Hours by Project:")
print(f"    {'ProjID':>8} {'Job#':>12} {'Description':>25} {'ActualHrs':>12}")
for row in cursor.fetchall():
    desc = str(row[2])[:25] if row[2] else ""
    print(f"    {row[0]:>8} {str(row[1] or ''):>12} {desc:>25} {row[3]:>12}")

subsection("8. ESTIMATED HOURS by Project (from productioncontroljobs)")
cursor.execute("""
    SELECT
        pcj.ProjectID,
        p.JobNumber,
        p.JobDescription,
        ROUND(pcj.TotalManHours, 2) as EstimatedHours
    FROM productioncontroljobs pcj
    LEFT JOIN projects p ON pcj.ProjectID = p.ProjectID
    WHERE pcj.TotalManHours IS NOT NULL AND pcj.TotalManHours > 0
    ORDER BY pcj.TotalManHours DESC
    LIMIT 10
""")
print("  Estimated Hours by Project:")
print(f"    {'ProjID':>8} {'Job#':>12} {'Description':>25} {'EstHours':>12}")
for row in cursor.fetchall():
    desc = str(row[2])[:25] if row[2] else ""
    print(f"    {str(row[0] or ''):>8} {str(row[1] or ''):>12} {desc:>25} {row[3]:>12}")

subsection("9. ESTIMATE vs ACTUAL Comparison")
cursor.execute("""
    SELECT
        p.JobNumber,
        p.JobDescription,
        ROUND(pcj.TotalManHours, 2) as EstimatedHours,
        ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours), 2) as ActualHours,
        ROUND(
            (SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours),
            2
        ) as Variance,
        ROUND(
            ((SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours) / pcj.TotalManHours) * 100,
            1
        ) as VariancePct
    FROM projects p
    JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
    JOIN timerecords tr ON p.ProjectID = tr.ProjectID
    WHERE pcj.TotalManHours IS NOT NULL AND pcj.TotalManHours > 0
    GROUP BY p.ProjectID, p.JobNumber, p.JobDescription, pcj.TotalManHours
    ORDER BY ABS((SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours) / pcj.TotalManHours) DESC
    LIMIT 15
""")
print("  ESTIMATE vs ACTUAL by Job:")
print(f"    {'Job#':>10} {'Description':>22} {'Est':>10} {'Actual':>10} {'Var':>10} {'Var%':>8}")
for row in cursor.fetchall():
    desc = str(row[1])[:22] if row[1] else ""
    print(f"    {str(row[0]):>10} {desc:>22} {row[2]:>10} {row[3]:>10} {row[4]:>10} {str(row[5])+'%':>8}")

subsection("10. Actual Hours by Station (for labor group comparison)")
cursor.execute("""
    SELECT
        s.Description as Station,
        ROUND(SUM(tr.RegularHours + tr.OvertimeHours), 2) as TotalHours
    FROM timerecords tr
    LEFT JOIN stations s ON tr.StationID = s.StationID
    GROUP BY s.StationID, s.Description
    ORDER BY TotalHours DESC
    LIMIT 15
""")
print("  Actual Hours by Station:")
for row in cursor.fetchall():
    print(f"    {str(row[0] or '(no station)'):>25}: {row[1]} hours")

cursor.close()
conn.close()

print("\n" + "=" * 75)
print("  EXPLORATION COMPLETE (ALL READ-ONLY)")
print("=" * 75)
