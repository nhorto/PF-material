# PowerFab Schema - Quick Reference Card

**Ultra-compact reference for SQL generation**

---

## Core Tables (10)

| Table | PK | Rows | Purpose |
|-------|-----|------|---------|
| `projects` | ProjectID | 226 | Master job records |
| `estimates` | EstimateID | 835 | Bid estimates |
| `estimateitems` | EstimateItemID | 301K | Parts in estimates |
| `estimateitemlaborgroups` | (EstimateItemID, LaborGroupID) | 2.4M | Hours by operation type |
| `productioncontroljobs` | ProductionControlID | 234 | Production jobs |
| `productioncontrolitemstations` | ProductionControlItemStationID | 50K | Piece completion tracking |
| `timerecords` | TimeRecordID | 26K | Actual labor hours |
| `stations` | StationID | 26 | Workstations |
| `laborgroups` | LaborGroupID | 22 | Operation categories |
| `stationlaborgroups` | StationLaborGroupID | 27 | Station↔LaborGroup mapping |

---

## Key Columns by Table

### projects
- `ProjectID` (PK), `JobNumber`, `JobDescription`

### estimates
- `EstimateID` (PK), `ProjectID` (FK), `JobNumber`, `JobName`, `TotalManHours`
- ⚠️ NOT: Description, TotalLabor

### estimateitems
- `EstimateItemID` (PK), `EstimateID` (FK), `ManHours`, `Quantity`

### estimateitemlaborgroups
- `EstimateItemID` (PK/FK), `LaborGroupID` (PK/FK), `ManHours`

### productioncontroljobs
- `ProductionControlID` (PK), `ProjectID` (FK), `EstimateID` (FK), `JobNumber`, `TotalManHours`

### productioncontrolitemstations
- `ProductionControlID` (FK), `MainMark`, `PieceMark`, `StationID`, `Hours`, `Quantity`, `DateCompleted`

### timerecords
- `TimeRecordID` (PK), `ProjectID` (FK), `StationID` (FK), `RegularHours`, `OvertimeHours`, `Overtime2Hours`, `DeductionHours`, `StartDate`
- ⚠️ NO: MainMark, PieceMark, Sequence

### stations
- `StationID` (PK), `Description`

### laborgroups
- `LaborGroupID` (PK), `Description`

### stationlaborgroups
- `StationID` (FK), `LaborGroupID` (FK)

---

## Join Paths

**Estimated Hours:**
```
estimates → estimateitems → estimateitemlaborgroups → laborgroups
```

**Actual Hours (Job Level):**
```
projects → timerecords → stations
```

**Production Tracking:**
```
productioncontroljobs → productioncontrolitemstations → stations
```

**Estimated vs Actual:**
```
projects ← productioncontroljobs → estimates → estimateitems → estimateitemlaborgroups
         ↓
    timerecords
```

**By Operation Type:**
```
laborgroups ← stationlaborgroups → stations ← timerecords
```

---

## Critical Rules

1. **Total Hours**: `RegularHours + OvertimeHours + Overtime2Hours` (NOT DeductionHours)
2. **No FKs**: All joins inferred, not enforced
3. **Two Time Systems**:
   - `timerecords` = job-level hours (for costing)
   - `productioncontrolitemstations` = piece-level tracking (for progress)
4. **Piece Marks**: Only in `productioncontrolitemstations`, NOT in `timerecords`
5. **Safe Division**: `value / NULLIF(divisor, 0)`

---

## Common Patterns

**Estimated vs Actual (Job):**
```sql
SELECT
    p.JobNumber,
    pcj.TotalManHours as Est,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as Act
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
LEFT JOIN timerecords tr ON p.ProjectID = tr.ProjectID
WHERE p.JobNumber = ?
GROUP BY p.JobNumber, pcj.TotalManHours
```

**Hours by Station:**
```sql
SELECT
    s.Description,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as Hrs
FROM timerecords tr
JOIN stations s ON tr.StationID = s.StationID
WHERE tr.ProjectID = ?
GROUP BY s.StationID, s.Description
```

**Estimated by Labor Group:**
```sql
SELECT
    lg.Description,
    SUM(eilg.ManHours) as Hrs
FROM estimateitemlaborgroups eilg
JOIN estimateitems ei ON eilg.EstimateItemID = ei.EstimateItemID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID
WHERE ei.EstimateID = ?
GROUP BY lg.LaborGroupID, lg.Description
```

---

## Lookup Values

**Sample Stations**:
- 1-Cut/Saw, Fab Fit, Fab Weld, QC Fitup Ins, Material Handling, Paint/Primer

**Sample Labor Groups**:
- Cut, Weld, Fit, Unload, GetPc

---

## Quick Checks

✅ Using `TotalManHours` (not TotalLabor)?
✅ Using `JobName` (not Description) for estimates?
✅ Summing all 3 hour types from timerecords?
✅ LEFT JOIN on timerecords (may have no actuals)?
✅ GROUP BY all non-aggregated columns?
✅ NULL-safe division?
