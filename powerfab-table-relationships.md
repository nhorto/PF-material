# PowerFab Table Relationships

## Tables That Matter for Time Tracking & Estimates

---

## Visual Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CORE REFERENCE TABLES                              │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │    users     │      │   projects   │      │   stations   │
    │──────────────│      │──────────────│      │──────────────│
    │ UserID (PK)  │      │ ProjectID(PK)│      │ StationID(PK)│
    │ Username     │      │ JobNumber    │      │ Description  │
    │ FirstName    │      │ JobDescription│     │ StationNumber│
    │ LastName     │      │ GroupName    │      │ DepartmentID │
    └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
           │                     │                     │
           │                     │                     │
           ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TIME TRACKING                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────────────┐
                         │      timerecords        │
                         │─────────────────────────│
                         │ TimeRecordID (PK)       │
    users.UserID ◄────── │ EmployeeUserID (FK)     │
    projects.ProjectID◄──│ ProjectID (FK)          │
    stations.StationID◄──│ StationID (FK)          │
                         │ StartDate               │
                         │ RegularHours            │
                         │ OvertimeHours           │
                         │ Overtime2Hours          │
                         │ DeductionHours          │
                         │ TimeRecordSubjectID (FK)│──┐
                         │ InProgress              │  │
                         └─────────────────────────┘  │
                                                      │
              ┌───────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  timerecordsubjectfieldmappings  │◄── Junction table
    │─────────────────────────────│
    │ TimeRecordSubjectID (FK)    │
    │ SubjectFieldID              │◄── Field type (1, 2, 32, 128)
    │ TimeRecordSubjectFieldID(FK)│──┐
    └─────────────────────────────┘  │
                                     │
              ┌──────────────────────┘
              ▼
    ┌─────────────────────────────┐
    │   timerecordsubjectfields   │
    │─────────────────────────────│
    │ TimeRecordSubjectFieldID(PK)│
    │ SubjectFieldValue           │◄── Actual text: "702", "B1-5", etc.
    └─────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION TRACKING                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────────────────────┐
    │    productioncontroljobs      │◄── The "production job" - links to estimates
    │───────────────────────────────│
    │ ProductionControlID (PK)      │
    │ ProjectID (FK)                │──────► projects.ProjectID
    │ EstimateID (FK)               │──────► estimates.EstimateID
    │ TotalManHours                 │◄── ESTIMATED hours (copied from estimate)
    │ TotalWeight                   │
    │ TotalQuantity                 │
    └───────────────┬───────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────────┐  ┌────────────────────────┐
│productioncontrol- │  │ productioncontrol-     │
│    sequences      │  │      items             │◄── Bill of Materials
│───────────────────│  │────────────────────────│
│ SequenceID (PK)   │  │ ProductionControlItemID│
│ ProductionControl-│  │ ProductionControlID(FK)│
│   ID (FK)         │  │ MainMark               │
│ Description       │  │ PieceMark              │
│ LotNumber         │  │ Quantity               │
└────────┬──────────┘  │ Weight                 │
         │             │ SequenceID (FK)        │──► productioncontrolsequences
         │             └────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ productioncontrolitemstations   │◄── Piece completion tracking
│─────────────────────────────────│
│ ProductionControlItemStationID  │
│ ProductionControlID (FK)        │──► productioncontroljobs
│ MainMark                        │
│ PieceMark                       │
│ SequenceID (FK)                 │──► productioncontrolsequences
│ StationID (FK)                  │──► stations
│ Quantity                        │
│ DateCompleted                   │
│ Hours                           │◄── Optional: timer-based hours
│ UserID (FK)                     │──► users
└─────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ESTIMATING                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────┐
    │       estimates         │
    │─────────────────────────│
    │ EstimateID (PK)         │◄───────── productioncontroljobs.EstimateID
    │ JobNumber               │
    │ JobName                 │
    │ TotalManHours           │◄── Total estimated hours
    │ TotalWeight             │
    │ Estimator               │
    └───────────┬─────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │     estimateitems       │◄── Piece-level estimates
    │─────────────────────────│
    │ EstimateItemID (PK)     │
    │ EstimateID (FK)         │──► estimates.EstimateID
    │ MainMark                │
    │ PieceMark               │
    │ Quantity                │
    │ ManHours                │◄── Estimated hours for this item
    │ ManHoursPerPiece        │◄── Hours per individual piece
    │ CalculatedManHours      │
    │ LaborCodeID             │
    └─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         LABOR GROUPS (Estimate ↔ Actual Bridge)                 │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────┐
    │      laborgroups        │◄── Categories of labor for estimating
    │─────────────────────────│
    │ LaborGroupID (PK)       │
    │ Description             │    (e.g., "Welding", "Fitting", "Cutting")
    └───────────┬─────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │   stationlaborgroups    │◄── Maps stations to labor groups
    │─────────────────────────│
    │ StationID (FK)          │──► stations.StationID
    │ LaborGroupID (FK)       │──► laborgroups.LaborGroupID
    └─────────────────────────┘

    This table answers: "Which labor group does this station belong to?"
    Used to compare estimated hours (by labor group) to actual hours (by station)
```

---

## Table Descriptions

### Core Reference Tables

#### `users`
**What it is:** List of all people in the system (employees, admins, etc.)

| Key Column | What it means |
|------------|---------------|
| `UserID` | Unique identifier for the person |
| `Username` | Login name |
| `FirstName`, `LastName` | Person's name |
| `Active` | Is this user still active? |
| `ProductionUser` | Is this a shop floor worker? |

**Connected to:**
- `timerecords.EmployeeUserID` → Who logged the time
- `productioncontrolitemstations.UserID` → Who completed the piece

---

#### `projects`
**What it is:** List of jobs/projects (customer contracts)

| Key Column | What it means |
|------------|---------------|
| `ProjectID` | Unique identifier for the project |
| `JobNumber` | Human-readable job number (e.g., "22039") |
| `JobDescription` | Project name (e.g., "Fuze Ballpark") |
| `GroupName` | Project manager or group |

**Connected to:**
- `timerecords.ProjectID` → Which job time was logged against
- `productioncontroljobs.ProjectID` → Links production to this project

---

#### `stations`
**What it is:** Work stations in the shop (areas where work happens)

| Key Column | What it means |
|------------|---------------|
| `StationID` | Unique identifier |
| `Description` | Station name (e.g., "1-Cut/Saw", "Fab Weld", "QC Fitup Ins") |
| `StationNumber` | Ordering number |
| `DepartmentID` | Which department owns this station |

**Connected to:**
- `timerecords.StationID` → Where time was spent
- `productioncontrolitemstations.StationID` → Where pieces were completed
- `stationlaborgroups.StationID` → Maps to labor groups for estimates

---

### Time Tracking Tables

#### `timerecords`
**What it is:** Every time entry in the system. One row = one clock-in/clock-out or time entry.

| Key Column | What it means |
|------------|---------------|
| `TimeRecordID` | Unique identifier |
| `EmployeeUserID` | Who worked (→ `users`) |
| `ProjectID` | Which job (→ `projects`) |
| `StationID` | Which station (→ `stations`) |
| `StartDate` | Date of work |
| `RegularHours` | Standard pay hours |
| `OvertimeHours` | 1.5x hours |
| `Overtime2Hours` | 2x hours |
| `DeductionHours` | Break/lunch time |
| `TimeRecordSubjectID` | Links to subject field system |
| `InProgress` | Is clock still running? (1=yes) |

**Connected to:**
- `users` via `EmployeeUserID`
- `projects` via `ProjectID`
- `stations` via `StationID`
- Subject field system via `TimeRecordSubjectID`

---

#### `timerecordsubjectfieldmappings`
**What it is:** Junction table that links a time record's subject to specific field values.

| Key Column | What it means |
|------------|---------------|
| `TimeRecordSubjectID` | Which subject (from timerecords) |
| `SubjectFieldID` | Type of field (1, 2, 32, or 128) |
| `TimeRecordSubjectFieldID` | Links to actual value |

**Purpose:** One time record can have multiple subject field values (e.g., both a sequence AND a piece mark).

---

#### `timerecordsubjectfields`
**What it is:** The actual text values that describe what was worked on.

| Key Column | What it means |
|------------|---------------|
| `TimeRecordSubjectFieldID` | Unique identifier |
| `SubjectFieldValue` | The actual text (e.g., "702", "B1-5", "70238A") |

**Examples of values:**
- `"702"` - Sequence number
- `"70238A"` - Piece mark
- `"Start at 5:16"` - Notes

---

### Production Tracking Tables

#### `productioncontroljobs`
**What it is:** Production jobs - the link between projects and estimates.

| Key Column | What it means |
|------------|---------------|
| `ProductionControlID` | Unique identifier for this production job |
| `ProjectID` | Links to `projects` table |
| `EstimateID` | Links to `estimates` table |
| `TotalManHours` | **Estimated hours** (copied from estimate) |
| `TotalWeight` | Total job weight |
| `TotalQuantity` | Total pieces |

**Why it matters:** This table is the **bridge** between estimates and actuals. It holds the estimated hours that you compare against actual time records.

---

#### `productioncontrolitems`
**What it is:** The Bill of Materials - every piece that needs to be fabricated.

| Key Column | What it means |
|------------|---------------|
| `ProductionControlItemID` | Unique identifier |
| `ProductionControlID` | Which job (→ `productioncontroljobs`) |
| `MainMark` | Assembly identifier (e.g., "B1") |
| `PieceMark` | Part identifier (e.g., "B1-5") |
| `Quantity` | How many to make |
| `Weight` | Piece weight |
| `SequenceID` | Which sequence (→ `productioncontrolsequences`) |

---

#### `productioncontrolsequences`
**What it is:** Sequences and lots - groupings of parts for scheduling/shipping.

| Key Column | What it means |
|------------|---------------|
| `SequenceID` | Unique identifier |
| `ProductionControlID` | Which job |
| `Description` | Sequence name/number (e.g., "1", "2", "Level 3") |
| `LotNumber` | Lot within the sequence |

---

#### `productioncontrolitemstations`
**What it is:** Piece completion tracking - records when each piece completes each station.

| Key Column | What it means |
|------------|---------------|
| `ProductionControlItemStationID` | Unique identifier |
| `ProductionControlID` | Which job |
| `MainMark` | Assembly |
| `PieceMark` | Part |
| `SequenceID` | Which sequence |
| `StationID` | Which station completed |
| `Quantity` | Pieces completed |
| `DateCompleted` | When |
| `Hours` | Time spent (if timer used) |
| `UserID` | Who completed it |

---

### Estimating Tables

#### `estimates`
**What it is:** The bid/estimate for a job.

| Key Column | What it means |
|------------|---------------|
| `EstimateID` | Unique identifier |
| `JobNumber` | Job reference |
| `JobName` | Job name |
| `TotalManHours` | Total estimated labor hours |
| `TotalWeight` | Total estimated weight |
| `Estimator` | Who created the estimate |

---

#### `estimateitems`
**What it is:** Individual items in the estimate - piece-level labor estimates.

| Key Column | What it means |
|------------|---------------|
| `EstimateItemID` | Unique identifier |
| `EstimateID` | Which estimate |
| `MainMark` | Assembly |
| `PieceMark` | Part |
| `Quantity` | How many |
| `ManHours` | Estimated hours for this line |
| `ManHoursPerPiece` | Hours per individual piece |
| `LaborCodeID` | Labor category |

---

### Labor Group Tables

#### `laborgroups`
**What it is:** Categories of labor used in estimating (e.g., "Welding", "Cutting", "Fitting").

| Key Column | What it means |
|------------|---------------|
| `LaborGroupID` | Unique identifier |
| `Description` | Group name |

---

#### `stationlaborgroups`
**What it is:** Maps production stations to estimating labor groups.

| Key Column | What it means |
|------------|---------------|
| `StationID` | Which station (→ `stations`) |
| `LaborGroupID` | Which labor group (→ `laborgroups`) |

**Why it matters:** This is how you connect estimated hours (organized by labor group) to actual hours (organized by station).

---

## Key Relationships Summary

| From Table | Column | To Table | Column | Meaning |
|------------|--------|----------|--------|---------|
| `timerecords` | `EmployeeUserID` | `users` | `UserID` | Who logged time |
| `timerecords` | `ProjectID` | `projects` | `ProjectID` | Which job |
| `timerecords` | `StationID` | `stations` | `StationID` | Which station |
| `productioncontroljobs` | `ProjectID` | `projects` | `ProjectID` | Links production to project |
| `productioncontroljobs` | `EstimateID` | `estimates` | `EstimateID` | Links production to estimate |
| `productioncontrolitems` | `ProductionControlID` | `productioncontroljobs` | `ProductionControlID` | BOM belongs to job |
| `productioncontrolitems` | `SequenceID` | `productioncontrolsequences` | `SequenceID` | Item belongs to sequence |
| `productioncontrolitemstations` | `ProductionControlID` | `productioncontroljobs` | `ProductionControlID` | Completion for job |
| `productioncontrolitemstations` | `StationID` | `stations` | `StationID` | Which station completed |
| `productioncontrolitemstations` | `SequenceID` | `productioncontrolsequences` | `SequenceID` | Which sequence |
| `estimateitems` | `EstimateID` | `estimates` | `EstimateID` | Item belongs to estimate |
| `stationlaborgroups` | `StationID` | `stations` | `StationID` | Maps station |
| `stationlaborgroups` | `LaborGroupID` | `laborgroups` | `LaborGroupID` | Maps to labor group |

---

## The Path: Estimate → Actual

```
estimates.TotalManHours
        │
        │ (copied when job created)
        ▼
productioncontroljobs.TotalManHours  ←── ESTIMATED HOURS
        │
        │ (via ProjectID)
        ▼
projects.ProjectID
        │
        │ (via ProjectID)
        ▼
SUM(timerecords.RegularHours + OvertimeHours)  ←── ACTUAL HOURS
```

**To compare estimate vs actual:**
1. Join `productioncontroljobs` to `projects` on `ProjectID`
2. Join `timerecords` to `projects` on `ProjectID`
3. Compare `productioncontroljobs.TotalManHours` to `SUM(timerecords hours)`
