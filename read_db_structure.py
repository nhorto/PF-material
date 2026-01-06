"""
READ-ONLY Database Explorer for Time Tracking Tables
This script ONLY runs SELECT/DESCRIBE/SHOW queries - NO WRITES
"""
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

print('=' * 60)
print('READ-ONLY DATABASE EXPLORATION')
print('=' * 60)

print('\n=== Tables containing "user" ===')
cursor.execute("SHOW TABLES LIKE '%user%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

print('\n=== DESCRIBE users ===')
cursor.execute('DESCRIBE users')
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25} Key:{row[3]}")

print('\n=== DESCRIBE projects ===')
cursor.execute('DESCRIBE projects')
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25} Key:{row[3]}")

print('\n=== DESCRIBE stations ===')
cursor.execute('DESCRIBE stations')
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25} Key:{row[3]}")

print('\n=== DESCRIBE timerecordsubjectfields ===')
cursor.execute('DESCRIBE timerecordsubjectfields')
for row in cursor.fetchall():
    print(f"  {row[0]:35} {str(row[1]):25} Key:{row[3]}")

print('\n=== Sample: timerecords (5 rows) ===')
cursor.execute('''
    SELECT TimeRecordID, ProjectID, EmployeeUserID, StartDate,
           RegularHours, OvertimeHours, TimeRecordSubjectID
    FROM timerecords LIMIT 5
''')
print(f"  {'ID':>6} {'ProjID':>8} {'EmpID':>8} {'StartDate':>12} {'RegHrs':>10} {'OTHrs':>10} {'SubjID':>8}")
for row in cursor.fetchall():
    print(f"  {row[0]:>6} {str(row[1]):>8} {str(row[2]):>8} {str(row[3]):>12} {str(row[4]):>10} {str(row[5]):>10} {str(row[6]):>8}")

print('\n=== Sample: users (5 rows - names only) ===')
cursor.execute('SELECT UserID, UserName, FirstName, LastName FROM users LIMIT 5')
for row in cursor.fetchall():
    print(f"  UserID:{row[0]} | {row[1]} | {row[2]} {row[3]}")

print('\n=== Sample: projects (5 rows) ===')
cursor.execute('SELECT ProjectID, JobNumber, ProjectName FROM projects LIMIT 5')
for row in cursor.fetchall():
    print(f"  ProjectID:{row[0]} | Job:{row[1]} | {row[2]}")

print('\n=== Sample: stations (5 rows) ===')
cursor.execute('SELECT StationID, StationName FROM stations LIMIT 5')
for row in cursor.fetchall():
    print(f"  StationID:{row[0]} | {row[1]}")

print('\n=== Sample: timerecordsubjectfields (all rows) ===')
cursor.execute('SELECT * FROM timerecordsubjectfields LIMIT 20')
for row in cursor.fetchall():
    print(f"  {row}")

print('\n=== Tables with "schedule" ===')
cursor.execute("SHOW TABLES LIKE '%schedule%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
conn.close()
print('\n' + '=' * 60)
print('Done - all queries were READ-ONLY')
print('=' * 60)
