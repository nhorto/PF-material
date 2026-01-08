# Estimating Schema Reference

**Purpose**: Tables containing estimated labor hours, costs, and labor breakdowns for job bidding.

---

## estimates

**Purpose**: Top-level estimate records for job bids.

**Row Count**: 835

**Key Columns**:
- `EstimateID` (PK) - Unique estimate identifier
- `JobNumber` - Customer-facing job identifier
- `JobName` - Project name
- `ProjectID` (FK → projects.ProjectID) - Links to project management
- `TotalManHours` - Sum of all estimated labor hours
- `TotalWeight` - Total tonnage
- `BidDate` - When estimate was created
- `JobStatusID` - Estimate status

**Typical Joins**:
```sql
-- Link to production control jobs
JOIN productioncontroljobs pcj ON pcj.EstimateID = estimates.EstimateID

-- Link to projects
JOIN projects p ON estimates.ProjectID = p.ProjectID
```

**Common Filters**:
- `WHERE TotalManHours > 0` - Exclude empty estimates
- `WHERE JobStatusID = <value>` - Filter by bid status

**Pitfalls**:
- Column is `JobName` not `Description`
- No `TotalLabor` column (labor cost calculated from items)
- Some estimates have no ProjectID (bid-only, not awarded)

---

## estimateitems

**Purpose**: Individual parts/assemblies within an estimate with detailed labor calculations.

**Row Count**: 301,700

**Key Columns**:
- `EstimateItemID` (PK)
- `EstimateID` (FK → estimates.EstimateID)
- `ItemID` - Sequence within estimate
- `MainMark` - NOT a column (see productioncontrolitemstations)
- `PieceMark` - NOT a column (see productioncontrolitemstations)
- `PartNumber` - Part identifier
- `Quantity` - Number of pieces
- `ManHours` - Total labor hours for this item
- `CalculatedManHours` - System-calculated hours (before manual overrides)
- `Weight` - Item weight
- `Length` - Item length
- `ShapeID` - Shape type reference
- `LaborCodeID` - Labor operation code
- `ProductionCodeID` - Production category
- `Sequence` - Grouping for scheduling

**Typical Joins**:
```sql
-- Get labor breakdown by labor group
JOIN estimateitemlaborgroups eilg ON eilg.EstimateItemID = ei.EstimateItemID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID

-- Roll up to estimate
JOIN estimates e ON ei.EstimateID = e.EstimateID
```

**Aggregation Patterns**:
```sql
-- Total hours by estimate
SELECT EstimateID, SUM(ManHours) FROM estimateitems GROUP BY EstimateID

-- Total hours by shape
SELECT ShapeID, SUM(ManHours * Quantity) FROM estimateitems GROUP BY ShapeID
```

**Pitfalls**:
- `ManHours` is per item, multiply by `Quantity` for total
- No direct piece mark column - use for material/cost, not piece tracking
- Many columns for costs (MaterialCost, DetailingCost, ErectCost, etc.)

---

## estimateitemlaborgroups

**Purpose**: Labor hour breakdown by labor group (operation type) for each estimate item.

**Row Count**: 2,447,900

**Key Columns**:
- `EstimateItemID` (PK, FK → estimateitems.EstimateItemID)
- `LaborGroupID` (PK, FK → laborgroups.LaborGroupID)
- `ManHours` - Estimated hours for this labor group on this item
- `CalculatedManHours` - System-calculated value

**Typical Joins**:
```sql
-- Estimated hours by labor group for a job
SELECT
    lg.Description,
    SUM(eilg.ManHours) as EstimatedHours
FROM estimateitemlaborgroups eilg
JOIN estimateitems ei ON eilg.EstimateItemID = ei.EstimateItemID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID
WHERE ei.EstimateID = <estimate_id>
GROUP BY lg.Description
```

**Aggregation Patterns**:
```sql
-- Compare to actual by mapping labor groups to stations
SELECT
    lg.Description as LaborGroup,
    SUM(eilg.ManHours) as Estimated,
    SUM(tr.RegularHours + tr.OvertimeHours) as Actual
FROM estimateitemlaborgroups eilg
JOIN estimateitems ei ON eilg.EstimateItemID = ei.EstimateItemID
JOIN estimates e ON ei.EstimateID = e.EstimateID
JOIN productioncontroljobs pcj ON e.EstimateID = pcj.EstimateID
JOIN timerecords tr ON pcj.ProjectID = tr.ProjectID
JOIN stationlaborgroups slg ON eilg.LaborGroupID = slg.LaborGroupID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID
WHERE tr.StationID = slg.StationID
  AND e.EstimateID = <estimate_id>
GROUP BY lg.Description
```

**Pitfalls**:
- One estimate item has MULTIPLE rows (one per labor group)
- Must SUM across labor groups to get total item hours
- Labor group hours don't include material/overhead - only fabrication labor

---

## Key Relationships

```
estimates (1) ──→ (many) estimateitems
estimateitems (1) ──→ (many) estimateitemlaborgroups
estimateitemlaborgroups (many) ──→ (1) laborgroups

estimates (1) ──→ (0-1) productioncontroljobs [via EstimateID]
estimates (many) ──→ (0-1) projects [via ProjectID]
```

**Inferred Relationships** (no enforced FKs):
- estimates.EstimateID = productioncontroljobs.EstimateID
- estimates.ProjectID = projects.ProjectID
- estimateitems.EstimateID = estimates.EstimateID

---

## Example Queries

**Q: Total estimated hours for a job**
```sql
SELECT
    e.JobNumber,
    e.TotalManHours
FROM estimates e
WHERE e.EstimateID = ?
```

**Q: Estimated hours by labor group**
```sql
SELECT
    lg.Description,
    SUM(eilg.ManHours) as TotalHours
FROM estimateitemlaborgroups eilg
JOIN estimateitems ei ON eilg.EstimateItemID = ei.EstimateItemID
JOIN laborgroups lg ON eilg.LaborGroupID = lg.LaborGroupID
WHERE ei.EstimateID = ?
GROUP BY lg.LaborGroupID, lg.Description
ORDER BY TotalHours DESC
```

**Q: Items with highest estimated labor**
```sql
SELECT
    ei.PartNumber,
    ei.Quantity,
    ei.ManHours,
    ei.ManHours * ei.Quantity as TotalHours
FROM estimateitems ei
WHERE ei.EstimateID = ?
ORDER BY TotalHours DESC
LIMIT 10
```
