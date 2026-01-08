# Reference Tables Schema

**Purpose**: Core lookup and reference tables used throughout the system.

---

## projects

**Purpose**: Master job/project records - the top-level container for all work.

**Row Count**: 226

**Key Columns**:
- `ProjectID` (PK) - Unique project identifier
- `JobNumber` - Customer-facing job identifier (display value)
- `JobDescription` - Project description/name
- `JobLocation` - Job site location
- `JobStatusID` - Current project status
- `JobDate` - Project start/award date
- `CustomerPONumber` - Customer purchase order
- `GroupName` - Project grouping/category
- `ERPJobNumber` - External ERP system job number
- `CostCenter` - Cost center code
- `ExternalProjectID` - External system reference

**Typical Joins**:
```sql
-- Link to production control
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID

-- Link to estimates
JOIN estimates e ON p.ProjectID = e.ProjectID

-- Link to time records
JOIN timerecords tr ON p.ProjectID = tr.ProjectID
```

**Common Filters**:
- `WHERE JobNumber = ?` - Specific job (user-facing identifier)
- `WHERE JobStatusID = ?` - Filter by status
- `WHERE JobDate BETWEEN ? AND ?` - Date range

**Pitfalls**:
- `JobNumber` is varchar, may contain non-numeric characters
- One project can have multiple production control jobs (rare)
- One project can have multiple estimates (revisions)
- Some projects exist without production control or estimates

---

## productioncontroljobs

**Purpose**: Production-side job record with bill of materials and manufacturing details.

**Row Count**: 234

**Key Columns**:
- `ProductionControlID` (PK)
- `JobNumber` - Job identifier (may differ from projects.JobNumber)
- `JobDescription` - Project description
- `ProjectID` (FK → projects.ProjectID) - Link to project record
- `EstimateID` (FK → estimates.EstimateID) - Link to source estimate
- `TotalManHours` - Total estimated hours (copied from estimate)
- `TotalWeight` - Total tonnage
- `TotalQuantity` - Total piece count
- `JobStatusID` - Production status
- `JobDate` - Production start date
- `ShippingDate` - Target ship date
- `Finalized` - Whether job is locked

**Typical Joins**:
```sql
-- Link to project
JOIN projects p ON pcj.ProjectID = p.ProjectID

-- Link to estimate
JOIN estimates e ON pcj.EstimateID = e.EstimateID

-- Link to items
JOIN productioncontrolitems pci ON pcj.ProductionControlID = pci.ProductionControlID

-- Link to time tracking (via project)
JOIN timerecords tr ON pcj.ProjectID = tr.ProjectID
```

**Common Filters**:
- `WHERE ProductionControlID = ?` - Specific production job
- `WHERE ProjectID = ?` - All production jobs for a project
- `WHERE EstimateID = ?` - Production job created from an estimate
- `WHERE TotalManHours > 0` - Jobs with labor estimates

**Pitfalls**:
- `TotalManHours` is copied from estimate (not dynamically calculated)
- `JobNumber` here may differ from `projects.JobNumber`
- Not all projects have a production control job
- Not all production jobs link to an estimate

---

## stations

**Purpose**: Workstations/operations in the fabrication workflow.

**Row Count**: 26

**Key Columns**:
- `StationID` (PK)
- `StationNumber` - Sequence/ordering number
- `Description` - Station name (e.g., "1-Cut/Saw", "Fab Weld")
- `StationType` - Type code
- `CostCodeID` - Cost accounting code
- `DepartmentID` - Department assignment

**Sample Stations**:
- 1-Cut/Saw
- QC Fitup Ins
- Final QC
- Fab Fit
- Fab Weld
- Material Handling
- Kitting
- Paint/Primer

**Typical Joins**:
```sql
-- Link to time records
JOIN timerecords tr ON s.StationID = tr.StationID

-- Link to production tracking
JOIN productioncontrolitemstations pcis ON s.StationID = pcis.StationID

-- Link to labor groups (for estimate comparison)
JOIN stationlaborgroups slg ON s.StationID = slg.StationID
JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
```

**Common Filters**:
- `WHERE StationID = ?` - Specific station
- `WHERE Description LIKE ?` - Search by name

**Pitfalls**:
- Station names include prefixes/numbers (not standardized)
- One station may map to multiple labor groups
- Some stations are inactive but still in table

---

## laborgroups

**Purpose**: Labor categories/operation types used in estimating (maps to stations for actual vs estimated comparison).

**Row Count**: 22

**Key Columns**:
- `LaborGroupID` (PK)
- `Number` - Labor group number (unique)
- `Description` - Operation name (e.g., "Cut", "Weld", "Fit")
- `LaborRateID` - Default labor rate
- `Activity` - Activity type code

**Sample Labor Groups**:
- Unload
- GetPc
- Cut
- Weld
- Fit

**Typical Joins**:
```sql
-- Link to estimate item hours
JOIN estimateitemlaborgroups eilg ON lg.LaborGroupID = eilg.LaborGroupID

-- Link to stations (for actual comparison)
JOIN stationlaborgroups slg ON lg.LaborGroupID = slg.LaborGroupID
JOIN stations s ON slg.StationID = s.StationID
```

**Common Filters**:
- `WHERE LaborGroupID = ?` - Specific labor group
- `WHERE Description LIKE ?` - Search by name

**Pitfalls**:
- Labor groups are estimating-side (planning)
- Stations are production-side (actual)
- Many-to-many relationship (one station can have multiple labor groups)

---

## stationlaborgroups

**Purpose**: Mapping between production stations and estimating labor groups (enables estimated vs actual comparison).

**Row Count**: 27

**Key Columns**:
- `StationLaborGroupID` (PK)
- `StationID` (FK → stations.StationID)
- `LaborGroupID` (FK → laborgroups.LaborGroupID)

**Purpose**: This table is the **critical bridge** for comparing:
- Estimated hours (by labor group)
- Actual hours (by station)

**Typical Joins**:
```sql
-- Compare estimated vs actual by operation type
SELECT
    lg.Description as Operation,
    SUM(eilg.ManHours) as EstimatedHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as ActualHours
FROM stationlaborgroups slg
JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
JOIN stations s ON slg.StationID = s.StationID
LEFT JOIN estimateitemlaborgroups eilg ON eilg.LaborGroupID = lg.LaborGroupID
LEFT JOIN timerecords tr ON tr.StationID = s.StationID
WHERE ...
GROUP BY lg.LaborGroupID, lg.Description
```

**Pitfalls**:
- Not all stations have labor group mappings
- Some labor groups map to multiple stations
- Must carefully join on BOTH sides to compare

---

## Key Relationships

```
projects (1) ──→ (0-many) productioncontroljobs
projects (1) ──→ (0-many) estimates
projects (1) ──→ (many) timerecords

productioncontroljobs (1) ──→ (0-1) estimates [via EstimateID]
productioncontroljobs (1) ──→ (0-1) projects [via ProjectID]

stations (many) ←──→ (many) laborgroups [via stationlaborgroups]
```

**Inferred Relationships** (no enforced FKs):
- All relationships above are inferred from column names, not enforced
- Join safety depends on application logic, not database constraints

---

## Example Queries

**Q: List all projects with production jobs**
```sql
SELECT
    p.JobNumber,
    p.JobDescription,
    pcj.ProductionControlID,
    pcj.TotalManHours
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
ORDER BY p.JobNumber
```

**Q: Find station-to-labor-group mappings**
```sql
SELECT
    s.Description as Station,
    lg.Description as LaborGroup
FROM stationlaborgroups slg
JOIN stations s ON slg.StationID = s.StationID
JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
ORDER BY s.Description, lg.Description
```

**Q: Projects with both estimates and actuals**
```sql
SELECT
    p.JobNumber,
    e.TotalManHours as EstimatedHours,
    SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) as ActualHours
FROM projects p
JOIN estimates e ON p.ProjectID = e.ProjectID
JOIN timerecords tr ON p.ProjectID = tr.ProjectID
GROUP BY p.JobNumber, e.TotalManHours
HAVING ActualHours > 0
```
