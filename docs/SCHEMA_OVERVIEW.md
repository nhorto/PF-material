# PowerFab Database Schema - LLM Query Generation Guide

**Database**: `fabrication` (MySQL)
**Purpose**: Generate correct SQL queries for labor, cost, and estimating analytics
**Last Updated**: 2026-01-07

---

## Quick Reference

**Total Tables**: 1,285
**Relevant for Analytics**: ~523
**Core Tables Documented**: 10

**Documentation Files**:
- `schema_estimating.md` - Estimate tables and labor breakdowns
- `schema_time_tracking.md` - Actual hours and production tracking
- `schema_reference_tables.md` - Projects, stations, and lookups

---

## Core Schema Map

```
ESTIMATING SIDE                     PRODUCTION SIDE                 TIME TRACKING
─────────────────                   ───────────────                 ─────────────

estimates                           productioncontroljobs           timerecords
│  EstimateID (PK)                  │  ProductionControlID (PK)    │  TimeRecordID (PK)
│  JobNumber                        │  ProjectID → projects         │  ProjectID → projects
│  TotalManHours                    │  EstimateID → estimates       │  StationID → stations
│  ProjectID → projects             │  TotalManHours                │  RegularHours
└──→ estimateitems                  │  TotalWeight                  │  OvertimeHours
     │  EstimateItemID (PK)         └──→ productioncontrol-         │  Overtime2Hours
     │  EstimateID (FK)                  itemstations                └──(aggregated,
     │  ManHours                         │  MainMark                      no piece marks)
     │  Quantity                         │  PieceMark
     └──→ estimateitem-                  │  StationID
          laborgroups                    │  Hours (optional)
          │  LaborGroupID                │  Quantity
          │  ManHours                    └──(piece-level
          └──(one row per                     tracking)
               labor group)

LOOKUP TABLES
─────────────

projects                    stations                laborgroups             stationlaborgroups
│  ProjectID (PK)          │  StationID (PK)       │  LaborGroupID (PK)    │  StationID (FK)
│  JobNumber               │  Description          │  Description          │  LaborGroupID (FK)
│  JobDescription          │  (Fab Weld,Cut,etc)   │  (Cut,Weld,Fit,etc)   └──(bridge table)
└──(master job record)     └──(actual operations)  └──(estimated ops)
```

---

## Critical Data Facts

### NO Foreign Key Constraints
- **All relationships are inferred** from column names
- Database will NOT enforce referential integrity
- Queries must handle potential orphaned records

### Hour Aggregation Rules
1. **Always sum all hour types**: `RegularHours + OvertimeHours + Overtime2Hours`
2. **Exclude deductions**: Do NOT include `DeductionHours` in totals
3. **Watch for NULLs**: Use `COALESCE` or `IFNULL` when needed

### Two Separate Time Tracking Systems
1. **timerecords**: Job/station aggregated hours (for costing)
   - Use for: payroll, job costing, estimated vs actual
   - NO piece marks - aggregated by job + station only

2. **productioncontrolitemstations**: Piece-level completion tracking
   - Use for: production progress, throughput, cycle times
   - Hours optional (depends on timer usage)

### Column Name Variations
- **estimates**: Has `JobName` (NOT `Description`)
- **estimates**: Has `TotalManHours` (NOT `TotalLabor`)
- **productioncontroljobs**: Has `JobNumber` (may differ from projects.JobNumber)
- **productioncontrolitemstations**: MainMark may contain special chars (0x01)

---

## Common Query Patterns

### Pattern 1: Estimated vs Actual Hours (Job Level)

**Use Case**: "What are the estimated vs actual man-hours for job X?"

```sql
SELECT
    p.JobNumber,
    p.JobDescription,
    pcj.TotalManHours as EstimatedHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as ActualHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours as Variance
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
LEFT JOIN timerecords tr ON p.ProjectID = tr.ProjectID
WHERE p.JobNumber = ?
GROUP BY p.JobNumber, p.JobDescription, pcj.TotalManHours
```

**Key Points**:
- Join through `projects` table (master record)
- LEFT JOIN on timerecords (job may not have actuals yet)
- Group by estimated hours to preserve in SELECT

---

### Pattern 2: Estimated vs Actual by Labor Group/Station

**Use Case**: "Compare estimated welding hours to actual welding hours for job X"

```sql
SELECT
    lg.Description as Operation,
    SUM(eilg.ManHours) as EstimatedHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as ActualHours
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
JOIN estimates e ON pcj.EstimateID = e.EstimateID
JOIN estimateitems ei ON e.EstimateID = ei.EstimateID
JOIN estimateitemlaborgroups eilg ON ei.EstimateItemID = eilg.EstimateItemID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID
JOIN stationlaborgroups slg ON lg.LaborGroupID = slg.LaborGroupID
LEFT JOIN timerecords tr ON p.ProjectID = tr.ProjectID AND tr.StationID = slg.StationID
WHERE p.JobNumber = ?
GROUP BY lg.LaborGroupID, lg.Description
ORDER BY EstimatedHours DESC
```

**Key Points**:
- Use `stationlaborgroups` to bridge labor groups (estimating) and stations (actual)
- LEFT JOIN on timerecords (may not have actuals for all operations)
- Must join on BOTH ProjectID AND StationID match

---

### Pattern 3: Total Hours by Station

**Use Case**: "How many hours were spent at the welding station this month?"

```sql
SELECT
    s.Description as Station,
    COUNT(DISTINCT tr.ProjectID) as NumJobs,
    COUNT(*) as TimeEntries,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as TotalHours
FROM timerecords tr
JOIN stations s ON tr.StationID = s.StationID
WHERE tr.StartDate BETWEEN ? AND ?
GROUP BY s.StationID, s.Description
ORDER BY TotalHours DESC
```

---

### Pattern 4: Estimated Hours by Labor Group

**Use Case**: "What are the estimated hours broken down by operation type for job X?"

```sql
SELECT
    lg.Description as LaborGroup,
    SUM(eilg.ManHours) as EstimatedHours,
    COUNT(DISTINCT ei.EstimateItemID) as NumItems
FROM estimates e
JOIN estimateitems ei ON e.EstimateID = ei.EstimateID
JOIN estimateitemlaborgroups eilg ON ei.EstimateItemID = eilg.EstimateItemID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID
WHERE e.EstimateID = ?
GROUP BY lg.LaborGroupID, lg.Description
ORDER BY EstimatedHours DESC
```

---

### Pattern 5: Production Throughput

**Use Case**: "How many pieces were completed at each station for job X?"

```sql
SELECT
    s.Description as Station,
    COUNT(DISTINCT pcis.MainMark) as UniqueAssemblies,
    SUM(pcis.Quantity) as TotalPieces,
    SUM(pcis.Hours) as TotalHours,
    SUM(pcis.Quantity) / NULLIF(SUM(pcis.Hours), 0) as PiecesPerHour
FROM productioncontrolitemstations pcis
JOIN productioncontroljobs pcj ON pcis.ProductionControlID = pcj.ProductionControlID
JOIN stations s ON pcis.StationID = s.StationID
WHERE pcj.JobNumber = ?
  AND pcis.Hours > 0
GROUP BY s.StationID, s.Description
ORDER BY TotalPieces DESC
```

---

### Pattern 6: Jobs with Largest Variance

**Use Case**: "Which jobs had the biggest difference between estimated and actual hours?"

```sql
SELECT
    p.JobNumber,
    p.JobDescription,
    pcj.TotalManHours as Estimated,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as Actual,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours as Variance,
    ROUND(
        (SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) / NULLIF(pcj.TotalManHours, 0) - 1) * 100,
        1
    ) as VariancePercent
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
LEFT JOIN timerecords tr ON p.ProjectID = tr.ProjectID
WHERE pcj.TotalManHours > 0
GROUP BY p.ProjectID, p.JobNumber, p.JobDescription, pcj.TotalManHours
HAVING Actual > 0
ORDER BY ABS(Variance) DESC
LIMIT 20
```

---

## Query Generation Rules

### Always Include
1. Table aliases for readability
2. Explicit JOIN conditions (never implicit comma joins)
3. GROUP BY for all non-aggregated SELECT columns
4. NULL handling for division (`NULLIF`, `COALESCE`)

### Always Avoid
1. SELECT * (specify needed columns)
2. Implicit type conversions
3. Unqualified column names when multiple tables have same column
4. Assuming foreign key enforcement

### Filtering Best Practices
1. Filter on indexed columns when possible:
   - `projects.JobNumber`
   - `estimates.EstimateID`
   - `timerecords.ProjectID`
   - `timerecords.StartDate`

2. Use parameter placeholders (`?`) for user input

3. Consider NULL possibilities:
   - `productioncontroljobs.EstimateID` can be NULL
   - `timerecords.EmployeeUserID` can be NULL
   - `productioncontrolitemstations.Hours` can be NULL

---

## MySQL-Specific Syntax

### Date Functions
```sql
-- Date range
WHERE StartDate BETWEEN '2024-01-01' AND '2024-12-31'

-- Current year
WHERE YEAR(StartDate) = YEAR(CURDATE())

-- Last 30 days
WHERE StartDate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
```

### Aggregation
```sql
-- Safe division
SUM(hours) / NULLIF(SUM(pieces), 0)

-- Percentage
ROUND((actual / NULLIF(estimated, 0) - 1) * 100, 1)

-- Conditional aggregation
SUM(CASE WHEN condition THEN value ELSE 0 END)
```

### String Handling
```sql
-- Case-insensitive search
WHERE JobNumber LIKE '%search%'

-- Concatenation
CONCAT(FirstName, ' ', LastName)
```

---

## Known Limitations

1. **No Sequences/Lots in timerecords**: Can't filter time by sequence or lot number
2. **No Piece Marks in timerecords**: Can't get time per specific piece from timerecords alone
3. **Station/Labor Group Mapping incomplete**: Not all stations map to labor groups
4. **Estimate LinkageOptional**: Not all production jobs have linked estimates
5. **Project Linkage Optional**: Some estimates never become projects

---

## Success Metrics

Query is correct if it:
1. ✅ Joins tables using correct foreign key columns
2. ✅ Aggregates hours correctly (Regular + Overtime + Overtime2)
3. ✅ Handles NULL values safely
4. ✅ Uses correct table for estimated vs actual
5. ✅ Groups by all non-aggregated columns
6. ✅ Returns results in reasonable format for dashboards

---

## Additional Context

- **Business Use**: Job costing, estimating feedback, capacity planning
- **Users**: Shop managers, estimators, project managers
- **Update Frequency**: Time records updated daily, estimates occasionally
- **Data Quality**: Generally high, but some manual entry errors possible
