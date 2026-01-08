# Time Tracking Schema Reference

**Purpose**: Tables tracking actual labor hours worked on jobs (for cost accounting and estimate validation).

---

## timerecords

**Purpose**: Labor time entries by employee, job, and station (aggregated, not piece-level).

**Row Count**: 26,211

**Key Columns**:
- `TimeRecordID` (PK)
- `ProjectID` (FK → projects.ProjectID) - Job being worked on
- `EmployeeUserID` (FK → users) - Worker who performed labor
- `StationID` (FK → stations.StationID) - Workstation/operation
- `StartDate` - Date of work
- `StartUnixTime` - Start timestamp (Unix epoch)
- `EndUnixTime` - End timestamp (Unix epoch)
- `RegularHours` - Standard hours worked
- `OvertimeHours` - Overtime hours (typically 1.5x pay)
- `Overtime2Hours` - Double overtime hours (typically 2x pay)
- `DeductionHours` - Non-billable time (breaks, lunch)
- `TimeRecordSubjectID` - Subject/category of work
- `ScheduleBaseTaskGlobalDescriptionID` - Link to project schedule task
- `InProgress` - Whether timer is still running

**NOT in this table**:
- Piece marks or main marks (aggregated at job/station level)
- Sequence or lot numbers
- Individual part tracking (see productioncontrolitemstations for piece-level)

**Typical Joins**:
```sql
-- Get job details
JOIN projects p ON tr.ProjectID = p.ProjectID

-- Get station/operation details
JOIN stations s ON tr.StationID = s.StationID

-- Get employee name
JOIN users u ON tr.EmployeeUserID = u.UserID
```

**Aggregation Patterns**:
```sql
-- Total hours by job
SELECT
    ProjectID,
    SUM(RegularHours + OvertimeHours + Overtime2Hours) as TotalHours
FROM timerecords
GROUP BY ProjectID

-- Total hours by station
SELECT
    StationID,
    SUM(RegularHours + OvertimeHours + Overtime2Hours) as TotalHours
FROM timerecords
GROUP BY StationID

-- Total hours by employee
SELECT
    EmployeeUserID,
    SUM(RegularHours + OvertimeHours + Overtime2Hours) as TotalHours
FROM timerecords
WHERE StartDate BETWEEN ? AND ?
GROUP BY EmployeeUserID
```

**Common Filters**:
- `WHERE ProjectID = ?` - Specific job
- `WHERE StationID = ?` - Specific operation
- `WHERE StartDate BETWEEN ? AND ?` - Date range
- `WHERE EmployeeUserID = ?` - Specific worker

**Pitfalls**:
- Always include ALL hour types: `RegularHours + OvertimeHours + Overtime2Hours`
- Exclude `DeductionHours` from billable totals
- No direct link to piece marks - this is job-level time tracking
- Some records have `EmployeeUserID = NULL` (bulk entries)
- `InProgress = 1` means timer still running (incomplete record)

---

## productioncontrolitemstations

**Purpose**: Piece-level production tracking - records completion of specific parts at stations, optionally with time.

**Row Count**: 50,022

**Key Columns**:
- `ProductionControlItemStationID` (PK)
- `ProductionControlID` (FK → productioncontroljobs.ProductionControlID) - Job
- `MainMark` - Assembly identifier (e.g., "B1", "C3")
- `PieceMark` - Piece identifier within assembly
- `SequenceID` - Sequence/shipment grouping
- `StationID` - Station where work completed
- `Quantity` - Number of pieces completed
- `Hours` - Labor hours (if tracked via timer)
- `UserID` - Employee who completed work
- `DateCompleted` - Completion date
- `TimeCompleted` - Completion time
- `BatchID` - Batch identifier
- `WorkAreaID` - Work area reference

**Typical Joins**:
```sql
-- Get job details
JOIN productioncontroljobs pcj ON pcis.ProductionControlID = pcj.ProductionControlID
JOIN projects p ON pcj.ProjectID = p.ProjectID

-- Get station details
JOIN stations s ON pcis.StationID = s.StationID

-- Get sequence details
JOIN productioncontrolsequences pcs ON pcis.SequenceID = pcs.SequenceID
```

**Aggregation Patterns**:
```sql
-- Total pieces completed by job and station
SELECT
    ProductionControlID,
    StationID,
    SUM(Quantity) as TotalPieces,
    SUM(Hours) as TotalHours
FROM productioncontrolitemstations
GROUP BY ProductionControlID, StationID

-- Throughput by station (pieces per hour)
SELECT
    StationID,
    SUM(Quantity) as TotalPieces,
    SUM(Hours) as TotalHours,
    SUM(Quantity) / NULLIF(SUM(Hours), 0) as PiecesPerHour
FROM productioncontrolitemstations
WHERE Hours > 0
GROUP BY StationID
```

**Common Filters**:
- `WHERE ProductionControlID = ?` - Specific job
- `WHERE MainMark = ?` - Specific assembly
- `WHERE StationID = ?` - Specific operation
- `WHERE DateCompleted BETWEEN ? AND ?` - Date range
- `WHERE Hours > 0` - Only records with time tracked

**Pitfalls**:
- `Hours` can be NULL or 0 (completion tracking without time)
- One physical piece may have multiple rows (once per station)
- `MainMark` may contain special characters (separator char: 0x01)
- Not all production uses this table - depends on job settings
- This is completion/progress tracking, not comprehensive time accounting

---

## Combining Time Sources

**Two types of time tracking in PowerFab**:

1. **timerecords**: Job-level labor hours (for costing)
   - Aggregated by job + station
   - Does NOT track individual pieces
   - Used for payroll and job costing

2. **productioncontrolitemstations**: Piece-level completion + optional hours
   - Tracks WHICH pieces completed WHICH stations
   - Hours optional (timer-based entry)
   - Used for production progress and throughput

**To analyze time at piece level**, must join both:

```sql
-- Allocate time records proportionally to pieces
SELECT
    pcis.MainMark,
    pcis.PieceMark,
    pcis.StationID,
    pcis.Quantity,
    pcis.Hours as PieceHours,
    tr_totals.StationHours as TotalStationHours
FROM productioncontrolitemstations pcis
JOIN productioncontroljobs pcj ON pcis.ProductionControlID = pcj.ProductionControlID
LEFT JOIN (
    SELECT
        ProjectID,
        StationID,
        SUM(RegularHours + OvertimeHours + Overtime2Hours) as StationHours
    FROM timerecords
    GROUP BY ProjectID, StationID
) tr_totals ON pcj.ProjectID = tr_totals.ProjectID
  AND pcis.StationID = tr_totals.StationID
WHERE pcj.ProjectID = ?
```

---

## Key Relationships

```
timerecords (many) ──→ (1) projects
timerecords (many) ──→ (1) stations
timerecords (many) ──→ (0-1) users [EmployeeUserID]

productioncontrolitemstations (many) ──→ (1) productioncontroljobs
productioncontrolitemstations (many) ──→ (1) stations
productioncontrolitemstations (many) ──→ (0-1) productioncontrolsequences
```

**Inferred Relationships** (no enforced FKs):
- timerecords.ProjectID = projects.ProjectID
- timerecords.StationID = stations.StationID
- productioncontrolitemstations.ProductionControlID = productioncontroljobs.ProductionControlID
- productioncontroljobs.ProjectID = projects.ProjectID

---

## Example Queries

**Q: Total actual hours for a job**
```sql
SELECT
    p.JobNumber,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as ActualHours
FROM timerecords tr
JOIN projects p ON tr.ProjectID = p.ProjectID
WHERE p.JobNumber = ?
GROUP BY p.JobNumber
```

**Q: Actual hours by station for a job**
```sql
SELECT
    s.Description as Station,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as TotalHours,
    COUNT(*) as TimeEntries
FROM timerecords tr
JOIN projects p ON tr.ProjectID = p.ProjectID
JOIN stations s ON tr.StationID = s.StationID
WHERE p.JobNumber = ?
GROUP BY s.StationID, s.Description
ORDER BY TotalHours DESC
```

**Q: Estimated vs Actual by job**
```sql
SELECT
    p.JobNumber,
    pcj.TotalManHours as EstimatedHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as ActualHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours as Variance,
    ROUND(
        (SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) / NULLIF(pcj.TotalManHours, 0) - 1) * 100,
        1
    ) as VariancePercent
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
LEFT JOIN timerecords tr ON p.ProjectID = tr.ProjectID
WHERE pcj.TotalManHours > 0
GROUP BY p.JobNumber, pcj.TotalManHours
HAVING ActualHours > 0
ORDER BY ABS(Variance) DESC
```

**Q: Pieces completed by main mark and station**
```sql
SELECT
    pcis.MainMark,
    s.Description as Station,
    SUM(pcis.Quantity) as PiecesCompleted,
    COUNT(DISTINCT pcis.PieceMark) as UniquePieces
FROM productioncontrolitemstations pcis
JOIN productioncontroljobs pcj ON pcis.ProductionControlID = pcj.ProductionControlID
JOIN stations s ON pcis.StationID = s.StationID
WHERE pcj.JobNumber = ?
GROUP BY pcis.MainMark, s.StationID, s.Description
ORDER BY pcis.MainMark, s.StationID
```
