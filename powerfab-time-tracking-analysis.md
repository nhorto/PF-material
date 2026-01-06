# Understanding Time Tracking in Tekla PowerFab

## A Technical and Conceptual Guide

---

## Table of Contents

1. [Overview: The Two Tracking Systems](#1-overview-the-two-tracking-systems)
2. [Time Tracking: Recording Labor Hours](#2-time-tracking-recording-labor-hours)
3. [Production Tracking: Recording Work Completion](#3-production-tracking-recording-work-completion)
4. [The Subject Field System: How Time Connects to Work](#4-the-subject-field-system-how-time-connects-to-work)
5. [Sequences and Lots: Organizing Work](#5-sequences-and-lots-organizing-work)
6. [The Estimating System: Where Estimates Live](#6-the-estimating-system-where-estimates-live)
7. [Connecting Everything: Estimate vs Actual](#7-connecting-everything-estimate-vs-actual)
8. [Key Database Tables Reference](#8-key-database-tables-reference)
9. [Sample Queries](#9-sample-queries)

---

## 1. Overview: The Two Tracking Systems

PowerFab uses **two separate but related systems** to track work on the shop floor:

| System | Purpose | Granularity | Key Question Answered |
|--------|---------|-------------|----------------------|
| **Time Tracking** | Records labor hours | Job + Station + Employee | "How many hours did we spend?" |
| **Production Tracking** | Records work completion | Piece Mark + Station | "What pieces are done?" |

### Why Two Systems?

This separation exists because of a fundamental trade-off in fabrication shops:

1. **Labor hours** need to be captured for job costing and payroll, but asking workers to log time for every individual piece would be impractical.

2. **Production completion** needs to track every piece through every station for scheduling and shipping, but doesn't always need detailed hour information.

The result: **Time tracking is aggregated** (hours at the job/station level), while **Production tracking is granular** (piece-by-piece status).

### Business Implications

- To know **total labor cost** for a job: Use time tracking
- To know **which pieces are complete**: Use production tracking
- To know **labor cost per piece**: Must combine both systems (more complex)

---

## 2. Time Tracking: Recording Labor Hours

### What is a Time Record?

A time record represents: "Employee X worked Y hours on Job Z at Station W on Date D."

### The `timerecords` Table

This is the main table that stores all time entries.

**Key Columns:**

| Column | Purpose | Links To |
|--------|---------|----------|
| `TimeRecordID` | Unique identifier (primary key) | - |
| `EmployeeUserID` | Who worked | `users.UserID` |
| `ProjectID` | Which job | `projects.ProjectID` |
| `StationID` | Which work station | `stations.StationID` |
| `StartDate` | Date work occurred | - |
| `StartUnixTime` / `EndUnixTime` | Exact time range | - |
| `RegularHours` | Standard pay hours | - |
| `OvertimeHours` | 1.5x pay hours | - |
| `Overtime2Hours` | 2x pay hours (double-time) | - |
| `DeductionHours` | Non-billable time (breaks) | - |
| `TimeRecordSubjectID` | What was worked on (flexible) | `timerecordsubjects` |
| `ScheduleBaseTaskGlobalDescriptionID` | Links to schedule task | Schedule tables |
| `InProgress` | Is the clock still running? | - |

### What's NOT Directly in Time Records

Notice that `timerecords` does **NOT** have:
- `SequenceID` - No direct link to sequences
- `LotID` - No direct link to lots
- `PieceMark` - No direct link to individual pieces

This is intentional. Time tracking is designed to be **quick and simple** for workers to enter. The detailed "what was worked on" information is stored through the **Subject Field System** (explained in Section 4).

### The Workflow: How Time Gets Entered

1. Worker clocks in or starts a time entry
2. They select:
   - The **Job** (project)
   - The **Station** (work area like "Welding" or "Cut/Saw")
   - Optionally: additional info through subject fields
3. Worker clocks out or completes the time entry
4. System calculates hours and stores the record

---

## 3. Production Tracking: Recording Work Completion

### What is Production Tracking?

Production tracking answers: "Has piece mark XYZ completed station ABC?"

Unlike time tracking (which records hours), production tracking records **completion status** at the piece level.

### The `productioncontrolitemstations` Table

This table records every piece's progress through each station.

**Key Columns:**

| Column | Purpose | Links To |
|--------|---------|----------|
| `ProductionControlItemStationID` | Unique identifier | - |
| `ProductionControlID` | Which production job | `productioncontroljobs` |
| `MainMark` | Assembly identifier (e.g., "B1") | - |
| `PieceMark` | Individual part (e.g., "B1-1") | - |
| `SequenceID` | Which sequence | `productioncontrolsequences` |
| `StationID` | Which station | `stations` |
| `Quantity` | How many pieces | - |
| `DateCompleted` | When completed | - |
| `TimeCompleted` | Time of day | - |
| `Hours` | Optional: time spent (from timer) | - |
| `UserID` | Who completed it | `users` |
| `BatchID` | For grouping related completions | - |

### The Bill of Materials: `productioncontrolitems`

Before pieces can be tracked through stations, they must be defined. The `productioncontrolitems` table is the **Bill of Materials** - it lists every piece that needs to be fabricated for a job.

**Key Columns:**

| Column | Purpose |
|--------|---------|
| `ProductionControlItemID` | Unique identifier |
| `ProductionControlID` | Which job |
| `MainMark` | Assembly identifier |
| `PieceMark` | Part identifier |
| `Quantity` | How many to make |
| `Weight` | Piece weight |
| `SequenceID` | Assigned sequence |

### The Workflow: How Production Gets Tracked

1. Bill of Materials is imported/created for a job
2. Each item is assigned a **Route** (list of stations it must pass through)
3. As work is completed:
   - Worker marks pieces complete at their station
   - System records the completion in `productioncontrolitemstations`
4. Management can see: "70% of Sequence 3 has completed Welding"

---

## 4. The Subject Field System: How Time Connects to Work

### The Problem

Time records need to capture "what was worked on" but:
- Can't have a direct foreign key to every possible thing (too complex)
- Different shops track different attributes
- Need flexibility for notes, sequence numbers, piece marks, etc.

### The Solution: A Flexible Key-Value System

PowerFab uses a **Subject Field System** - a flexible way to attach any text information to a time record.

### How It Works

```
timerecords.TimeRecordSubjectID
        │
        ▼
timerecordsubjectfieldmappings (junction table)
        │
        ├── SubjectFieldID = 1, 2, 32, or 128 (different field types)
        │
        ▼
timerecordsubjectfields.SubjectFieldValue (the actual text)
```

### What Gets Stored in Subject Fields

Based on the database exploration, the subject field values contain:

| SubjectFieldID | Typical Content | Examples |
|----------------|-----------------|----------|
| 1 | Simple identifiers | "1", "2" |
| 2 | Sequence numbers | "303", "401", "501" |
| 32 | Piece marks | "2A108", "70204A", "501121A" |
| 128 | Notes/comments | "Start at 5:16", "Forgot to clock out for lunch" |

### Example: Decoding a Time Record

When you see a time record with `TimeRecordSubjectID = 17`, you would:

1. Look up rows in `timerecordsubjectfieldmappings` where `TimeRecordSubjectID = 17`
2. For each row, get the `TimeRecordSubjectFieldID`
3. Look up that ID in `timerecordsubjectfields` to get the actual value

The result might be:
- Sequence: "702"
- PieceMark: "70238A"

This tells you the worker was working on Sequence 702, specifically piece 70238A.

### Why This Design?

1. **Flexibility**: Shops can track whatever attributes matter to them
2. **Performance**: Time entry stays fast (workers select from lists, not type piece marks)
3. **Extensibility**: New field types can be added without schema changes

---

## 5. Sequences and Lots: Organizing Work

### What is a Sequence?

A **Sequence** is a grouping of parts that:
- Ship together
- Follow the same production path
- Are scheduled as a unit

Think of it as a "work package" or "shipment batch."

Examples: "Level 2 Steel", "Sequence 3", "Truck Load A"

### What is a Lot?

A **Lot** is a sub-grouping within a sequence, often representing:
- A day's production batch
- A sub-assembly within a sequence
- A breakdown for scheduling purposes

### The `productioncontrolsequences` Table

This table defines sequences and lots for each job.

**Key Columns:**

| Column | Purpose |
|--------|---------|
| `SequenceID` | Unique identifier |
| `ProductionControlID` | Which job |
| `Description` | Sequence name/number |
| `LotNumber` | Lot within the sequence |
| `WorkPackageID` | Links to work packages |

### How Sequences Connect to Time

**Important**: `timerecords` does NOT have a `SequenceID` column.

Instead, sequence information is captured through the Subject Field System:
- When workers enter time, they may select a sequence
- That sequence identifier gets stored as a SubjectFieldValue
- To query "hours by sequence," you must join through the subject field tables

### How Sequences Connect to Production Tracking

**Direct Link**: `productioncontrolitemstations.SequenceID` directly references `productioncontrolsequences.SequenceID`.

This means production tracking has a cleaner path to sequence information than time tracking.

---

## 6. The Estimating System: Where Estimates Live

### The Purpose of Estimates

Before fabrication begins, estimators bid on jobs. They estimate:
- Material costs
- Labor hours (by labor group)
- Total man-hours

These estimates become the baseline for comparing actual performance.

### Key Estimating Tables

#### `estimates`

The main estimate record for a job.

**Key Columns:**

| Column | Purpose |
|--------|---------|
| `EstimateID` | Unique identifier |
| `JobNumber` | Job reference |
| `JobName` | Job description |
| `TotalManHours` | Total estimated labor hours |
| `TotalWeight` | Total estimated weight |
| `ShopDrawingHours` | Estimated detailing hours |
| `Estimator` | Who created the estimate |

#### `estimateitems`

Individual items in the estimate (piece-level estimates).

**Labor-related Columns:**

| Column | Purpose |
|--------|---------|
| `ManHours` | Estimated hours for this item |
| `ManHoursPerPiece` | Hours per individual piece |
| `CalculatedManHours` | System-calculated hours |
| `DetailingHours` | Drawing/detailing time |
| `ErectHours` | Erection time (on-site) |
| `LaborCodeID` | Links to labor rate codes |

### Labor Groups

Labor Groups categorize work types for estimating purposes.

#### `laborgroups` Table

| Column | Purpose |
|--------|---------|
| `LaborGroupID` | Unique identifier |
| `Description` | Group name (e.g., "Welding", "Fitting", "Cutting") |

#### `stationlaborgroups` Table

This **critical table** maps production stations to estimating labor groups.

| Column | Purpose |
|--------|---------|
| `StationID` | The production station |
| `LaborGroupID` | The corresponding labor group |

This mapping is **the bridge** between:
- **Estimated hours** (organized by Labor Group)
- **Actual hours** (organized by Station)

---

## 7. Connecting Everything: Estimate vs Actual

### The Goal

Compare: "How many hours did we estimate?" vs "How many hours did we actually spend?"

This can be done at multiple levels:
1. **Job Level**: Total hours for entire project
2. **Station/Labor Group Level**: Hours by work type
3. **Piece Level**: Hours per piece (requires combining systems)

### The Connection Path

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ESTIMATING SIDE                               │
├──────────────────────────────────────────────────────────────────────┤
│  estimates.TotalManHours         = Total estimated hours for job     │
│  estimates.EstimateID            ─────────────────────┐              │
│                                                       │              │
│  estimateitems.ManHours          = Per-piece estimates│              │
│  estimateitems.LaborCodeID       = Labor category     │              │
│                                                       │              │
│  laborgroups.Description         = "Welding", "Cutting", etc.       │
└───────────────────────────────────────────────────────│──────────────┘
                                                        │
                                                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   PRODUCTION CONTROL (The Bridge)                    │
├──────────────────────────────────────────────────────────────────────┤
│  productioncontroljobs.EstimateID      ◄──────────────┘              │
│  productioncontroljobs.ProjectID       ─────────────────┐            │
│  productioncontroljobs.TotalManHours   = Estimated hours (copied)   │
│                                                         │            │
│  stationlaborgroups                    = Maps stations to labor grps │
└─────────────────────────────────────────────────────────│────────────┘
                                                          │
                                                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        ACTUAL SIDE                                   │
├──────────────────────────────────────────────────────────────────────┤
│  projects.ProjectID                ◄────────────────────┘            │
│                                                                      │
│  timerecords.ProjectID             = Links to project                │
│  timerecords.StationID             = Where work was done             │
│  timerecords.RegularHours + OT     = Actual hours worked             │
│                                                                      │
│  SUM(timerecords hours)            = Total actual hours for job      │
└──────────────────────────────────────────────────────────────────────┘
```

### Job-Level Comparison

To compare estimate vs actual at the job level:

1. Get **Estimated Hours** from `productioncontroljobs.TotalManHours`
2. Get **Actual Hours** by summing `timerecords` for that `ProjectID`
3. Calculate variance: `Actual - Estimated`

### Station-Level Comparison

To compare by station/labor group:

1. Get **Estimated Hours by Labor Group** from `estimateitems` grouped by `LaborCodeID`
2. Get **Actual Hours by Station** from `timerecords` grouped by `StationID`
3. Use `stationlaborgroups` to map stations to labor groups
4. Compare corresponding groups

### Piece-Level Comparison (Most Complex)

To compare at the piece level requires combining:

1. **Estimated piece hours** from `estimateitems.ManHoursPerPiece`
2. **Actual piece hours** from either:
   - `productioncontrolitemstations.Hours` (if timer feature used)
   - Derived from time tracking through subject fields (complex)

---

## 8. Key Database Tables Reference

### Time Tracking Tables

| Table | Purpose |
|-------|---------|
| `timerecords` | Main time entry records |
| `timerecordsubjects` | Subject identifiers (just ID + hash) |
| `timerecordsubjectfields` | Actual subject values (text) |
| `timerecordsubjectfieldmappings` | Links time records to subject fields |
| `scheduletasktimerecords` | Links time records to schedule tasks |

### Production Tracking Tables

| Table | Purpose |
|-------|---------|
| `productioncontroljobs` | Production jobs (links to estimates) |
| `productioncontrolitems` | Bill of Materials (all pieces) |
| `productioncontrolitemstations` | Piece completion tracking |
| `productioncontrolsequences` | Sequence and lot definitions |

### Reference Tables

| Table | Purpose |
|-------|---------|
| `users` | Employee information |
| `projects` | Project/job information |
| `stations` | Work station definitions |
| `laborgroups` | Labor categories for estimating |
| `stationlaborgroups` | Maps stations to labor groups |

### Estimating Tables

| Table | Purpose |
|-------|---------|
| `estimates` | Main estimate records |
| `estimateitems` | Piece-level estimates |

---

## 9. Sample Queries

### Query 1: Actual Hours by Project

```sql
SELECT
    p.JobNumber,
    p.JobDescription,
    ROUND(SUM(tr.RegularHours), 2) as RegularHours,
    ROUND(SUM(tr.OvertimeHours), 2) as OvertimeHours,
    ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours), 2) as TotalActualHours
FROM timerecords tr
JOIN projects p ON tr.ProjectID = p.ProjectID
GROUP BY p.ProjectID, p.JobNumber, p.JobDescription
ORDER BY TotalActualHours DESC
```

### Query 2: Actual Hours by Employee

```sql
SELECT
    u.FirstName,
    u.LastName,
    COUNT(*) as TimeEntries,
    ROUND(SUM(tr.RegularHours + tr.OvertimeHours), 2) as TotalHours
FROM timerecords tr
JOIN users u ON tr.EmployeeUserID = u.UserID
GROUP BY u.UserID, u.FirstName, u.LastName
ORDER BY TotalHours DESC
```

### Query 3: Actual Hours by Station

```sql
SELECT
    s.Description as StationName,
    COUNT(*) as Entries,
    ROUND(SUM(tr.RegularHours + tr.OvertimeHours), 2) as TotalHours
FROM timerecords tr
LEFT JOIN stations s ON tr.StationID = s.StationID
GROUP BY s.StationID, s.Description
ORDER BY TotalHours DESC
```

### Query 4: Time Records with Subject Details (Sequence/Piece Info)

```sql
SELECT
    tr.TimeRecordID,
    tr.StartDate,
    u.FirstName as Worker,
    p.JobNumber,
    s.Description as Station,
    ROUND(tr.RegularHours, 2) as Hours,
    GROUP_CONCAT(tsf.SubjectFieldValue SEPARATOR ' | ') as WorkedOn
FROM timerecords tr
LEFT JOIN users u ON tr.EmployeeUserID = u.UserID
LEFT JOIN projects p ON tr.ProjectID = p.ProjectID
LEFT JOIN stations s ON tr.StationID = s.StationID
LEFT JOIN timerecordsubjectfieldmappings tsfm
    ON tr.TimeRecordSubjectID = tsfm.TimeRecordSubjectID
LEFT JOIN timerecordsubjectfields tsf
    ON tsfm.TimeRecordSubjectFieldID = tsf.TimeRecordSubjectFieldID
GROUP BY tr.TimeRecordID, tr.StartDate, u.FirstName, p.JobNumber, s.Description, tr.RegularHours
ORDER BY tr.StartDate DESC
LIMIT 100
```

### Query 5: Estimate vs Actual at Job Level

```sql
SELECT
    p.JobNumber,
    p.JobDescription,
    ROUND(pcj.TotalManHours, 2) as EstimatedHours,
    ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours), 2) as ActualHours,
    ROUND(SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours, 2) as Variance,
    ROUND(
        ((SUM(tr.RegularHours + tr.OvertimeHours + tr.Overtime2Hours) - pcj.TotalManHours)
        / pcj.TotalManHours) * 100, 1
    ) as VariancePercent
FROM projects p
JOIN productioncontroljobs pcj ON p.ProjectID = pcj.ProjectID
JOIN timerecords tr ON p.ProjectID = tr.ProjectID
WHERE pcj.TotalManHours > 0
GROUP BY p.ProjectID, p.JobNumber, p.JobDescription, pcj.TotalManHours
ORDER BY ABS(Variance) DESC
```

### Query 6: Production Tracking - Pieces Completed by Station

```sql
SELECT
    pcis.ProductionControlID as JobID,
    s.Description as Station,
    COUNT(*) as CompletionRecords,
    SUM(pcis.Quantity) as TotalPiecesCompleted
FROM productioncontrolitemstations pcis
JOIN stations s ON pcis.StationID = s.StationID
WHERE pcis.DateCompleted IS NOT NULL
GROUP BY pcis.ProductionControlID, s.StationID, s.Description
ORDER BY JobID, Station
```

### Query 7: Sequences for a Job

```sql
SELECT
    pcs.SequenceID,
    pcs.Description as SequenceName,
    pcs.LotNumber,
    COUNT(pci.ProductionControlItemID) as ItemsInSequence
FROM productioncontrolsequences pcs
LEFT JOIN productioncontrolitems pci ON pcs.SequenceID = pci.SequenceID
WHERE pcs.ProductionControlID = [YOUR_JOB_ID]
GROUP BY pcs.SequenceID, pcs.Description, pcs.LotNumber
ORDER BY pcs.Description
```

### Query 8: Station to Labor Group Mapping

```sql
SELECT
    s.StationID,
    s.Description as StationName,
    lg.LaborGroupID,
    lg.Description as LaborGroupName
FROM stationlaborgroups slg
JOIN stations s ON slg.StationID = s.StationID
JOIN laborgroups lg ON slg.LaborGroupID = lg.LaborGroupID
ORDER BY s.Description
```

---

## Summary

### Key Concepts to Remember

1. **Two Tracking Systems**: Time Tracking (hours) and Production Tracking (completion) serve different purposes and have different granularity.

2. **Subject Field System**: Time records connect to sequences/pieces through a flexible key-value system, not direct foreign keys.

3. **The Bridge Tables**:
   - `productioncontroljobs` links production to estimates
   - `stationlaborgroups` maps stations to labor groups

4. **Estimate vs Actual Path**:
   - Estimated hours: `estimates` → `productioncontroljobs.TotalManHours`
   - Actual hours: `timerecords` summed by `ProjectID`
   - Compare using the project as the common key

5. **For Piece-Level Analysis**: You must combine time tracking data with production tracking data, using shared dimensions (Job, Station, Date, potentially Subject Fields) to allocate hours to pieces.

---

*This document was created to help understand the PowerFab database structure for time tracking and estimate comparison purposes. All queries shown are READ-ONLY SELECT statements.*
