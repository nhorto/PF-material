**Understanding Time Tracking in Tekla PowerFab**
*A Conceptual Guide for Analytics and Extension Development*
Prepared for Nicholas | January 2026
# 1. Real-World Context: What Happens on the Shop Floor
Before diving into PowerFab's data structures, it's essential to understand what actually happens when a fabrication worker "logs time." This real-world understanding will inform every architectural decision you make.
## 1.1 The Physical Reality of Steel Fabrication
A steel fabrication shop transforms raw steel into finished structural components. The typical workflow involves receiving raw material (wide flange beams, angles, plates, tubes), then moving that material through a series of operations until it becomes a finished assembly ready to ship to a job site. Each operation represents a discrete transformation: cutting stock to length, drilling or punching holes, welding pieces together, grinding, painting, and finally loading onto trucks.
The key insight is that fabrication shops don't just track "time worked" in the abstract. They track time against specific work items because they need to understand three things: (1) Is this job going to be profitable? (2) Are our labor estimates accurate? (3) Where are the bottlenecks in our shop?
## 1.2 What Workers Actually Log Time Against
In practice, shop floor workers log time against a combination of attributes that together identify what they worked on. The primary dimensions are:
**Job** - The customer project (e.g., "Smith Office Building" or "Highway 101 Bridge"). This is the top-level container for all work.
**Station** - The workstation or operation type (e.g., "Cut/Saw", "Fit-Up", "Weld", "Paint"). This represents WHERE in the shop and WHAT type of work.
**Sequence** - A grouping of parts that ship together or follow the same production path (e.g., "Level 2 Steel" or "Sequence 3"). Think of this as a work package.
**Lot** - A sub-grouping within a sequence, often representing a day's production batch or a truck load.
**Task** - A specific schedule item from the project schedule (connects time to planned activities).
Critically, in PowerFab's standard time tracking workflow, workers do NOT directly log time against individual parts or piece marks. The system tracks production completion at the part level separately through "production tracking" (what piece marks have passed through what stations), while time tracking aggregates labor hours at the station/sequence/lot level. This is a deliberate design choice that balances accuracy with practical data entry on the shop floor.
## 1.3 Granularity in Real Practice
The granularity of time tracking varies significantly between shops based on their size, sophistication, and job costing requirements. There's a fundamental tension between data accuracy and data entry burden. PowerFab offers flexibility, but here's what's typical:

PowerFab Go (the mobile app) supports a "timer" feature that workers can start when beginning work on a piece or batch and stop when complete. The system then divides the recorded time across the pieces in the batch. This provides piece-level time data without requiring workers to enter times manually for each part.

# 2. PowerFab's Conceptual Model
Now let's map the real-world concepts to PowerFab's object model. Understanding this structure is crucial for building analytics that align with how data is actually stored and related.
## 2.1 The Core Object Hierarchy
PowerFab organizes fabrication data in a hierarchical structure. At the top is the Job, which represents a customer contract or project. Inside a job lives the Production Control Bill of Materials, which contains all the individual items (parts and assemblies) to be fabricated. Here's the key hierarchy:
**Production Control Job**
Bill of Materials (list of all items)
Main Marks (assemblies, like "B1" for Beam 1)
Piece Marks (individual parts within assemblies)
Sequences (groupings for scheduling and shipping)
Lots (sub-groupings within sequences)
Routes (which stations each item must pass through)
Project Schedule (Gantt chart of tasks)
Time Tracking Records (actual labor entries)
## 2.2 Stations and Routes
A Station represents a specific operation or area in the production workflow. Typical stations include Cut/Saw, Fit-Up, Weld, Blast/Clean, Paint, and Ship. Stations are defined globally (in Maintenance > Production Control > Station and Route Setup) and are available across all jobs.
A Route is an ordered list of stations that defines the production path for an item. For example, a simple beam might follow Route 1: Cut → Fit → Weld → Paint → Ship, while a complex connection might follow Route 2: Cut → Drill → Fit → Weld → Grind → Paint → Ship. Each item in the bill of materials is assigned a route, which determines what stations it must pass through.
Importantly, stations can be linked to Labor Groups from estimating. This connection allows PowerFab to associate estimated labor (from the bid) with actual labor (tracked in production) at the station level, enabling estimate-vs-actual comparison.
## 2.3 The Two Tracking Systems
PowerFab distinguishes between two related but separate tracking concepts:
**Production Tracking** records WHAT pieces have completed WHICH stations. This is completion status data: "Piece mark B1-1 completed the Weld station on 1/5/2026 by John Smith." Production tracking can optionally include labor time (via the timer feature), but its primary purpose is progress visibility.
**Time Tracking** records HOW MANY HOURS were spent by WHOM on WHAT dimensions (job, station, sequence, lot, task). This is labor hours data: "Mike worked 4 regular hours + 1 overtime hour on Job 2024-001, Weld station, Sequence 3 on 1/5/2026." Time tracking is about cost accumulation, not progress status.
For your analytics work, you'll likely need both data streams. Production tracking tells you throughput (pieces per day, cycle times). Time tracking tells you labor consumption (man-hours per ton, cost per job).

# 3. Time Tracking Workflows
Let's walk through exactly how time gets recorded in PowerFab, from the worker's perspective through to the database.
## 3.1 Data Entry Methods
PowerFab supports multiple methods for entering time tracking data, each suited to different shop environments:
**PowerFab Desktop - Time Tracking Input: **Within the Project Schedule dialog, supervisors or workers can use Maintenance > Time Tracking > Time Tracking Input to enter records. They select the start/end datetime, employee, job, station, sequence, lot, and task. Hours are auto-calculated from the time range, then allocated to regular, overtime, double-overtime, and deduction buckets.
**PowerFab Go Mobile App: **Shop floor workers can enter time directly from tablets or phones. They select a job, then enter employee, station, and other attributes configured by the admin. The app supports both manual time entry and timer-based entry.
**Excel Import: **Shops can import time tracking records from Excel files via Time Tracking Detail > Import Time Tracking Records. This is useful for integrating with external time clock systems or batch-loading historical data.
**API Integration: **The PowerFab Open API allows programmatic creation of time tracking records, enabling integration with shop floor automation systems, badge readers, or custom mobile apps.
## 3.2 Anatomy of a Time Tracking Record
Each time tracking record in PowerFab contains the following fields (not all are required in every configuration):

Notice that the time tracking record does NOT include piece marks directly. Time is recorded at the station/sequence/lot level and associated with jobs, not individual parts. If you need part-level time data, you would combine time tracking data with production tracking data (which does include piece marks).
## 3.3 Time Tracking Settings
PowerFab administrators can configure time tracking behavior globally and per-job. Key settings include whether overlapping time records are allowed (same employee, overlapping times), which fields are required vs optional in the mobile app, how hours are calculated from time ranges, and what pay categories are available. Understanding these settings is important for analytics because they affect data quality and completeness.

# 4. Why This Data Exists: Business Use Cases
Understanding why fabrication shops collect time data will help you design analytics that actually get used. The data serves several business-critical functions.
## 4.1 Job Costing and Profitability
The primary purpose of time tracking is job costing. When PowerFab links a production control job to an estimating job, it can compare estimated labor hours (from the bid) to actual labor hours (from time tracking). This comparison happens at multiple levels:
**Total job level: **Did we spend more or fewer hours than estimated for the whole project?
**Station level: **Did welding take longer than estimated? Was fit-up faster?
**Labor group level: **Were our estimates for specific operations accurate?
The "Compare to Estimating Job" feature in PowerFab displays estimated hours (by labor group, left side) against actual hours (by station, right side). This requires labor groups to be assigned to stations during station setup, creating the mapping between estimating categories and production stations.
## 4.2 Labor Rate Application
PowerFab's estimating module calculates labor costs by applying hourly rates to time. The labor database contains labor standards (time to perform operations like cutting, drilling, welding) and labor rates (dollars per hour for different labor types). When actual time is tracked, it can be costed by applying the appropriate rates, factoring in overtime multipliers. This gives real-time visibility into labor cost accumulation.
## 4.3 Production Scheduling
Time tracking feeds into both the Project Schedule (Gantt chart) and the Production Schedule (resource allocation view). When time is logged against a schedule task, PowerFab updates the actual hours on that task, allowing comparison of planned vs actual hours. Tasks where actual hours exceed planned are highlighted, signaling potential schedule slippage.
The production schedule shows capacity utilization by resource (workstation, shop area, or generic "Shop" resource). When time tracking records include task associations, the actual hours appear on the production schedule, helping shop managers understand true capacity consumption vs allocation.
## 4.4 Estimating Feedback Loop
Perhaps the most valuable long-term use of time tracking data is improving future estimates. By analyzing historical time data across completed jobs, estimators can calibrate their labor standards. For example, if time tracking consistently shows that welding complex connections takes 20% longer than estimated, those labor standards can be adjusted. This feedback loop is essential for competitive bidding while maintaining profitability.

# 5. Mental Model: How Everything Connects
Here's a conceptual diagram (described in text) showing how the key objects relate. This mental model should help you reason about the data without looking at actual tables.
## 5.1 The Object Relationship Model
─── ESTIMATING SIDE ───                    ─── PRODUCTION SIDE ───

[Estimating Job]                           [Production Control Job]
│                                           │
│ (linked via Production Codes)            │
│                                           │
[Labor Groups] ◄────────────────────────► [Stations]
│                                           │
[Estimated Hours]                        [Routes]
│
[Bill of Materials]
│
┌──────────────┼──────────────┐
│              │              │
[Main Marks]   [Sequences]    [Lots]
│
[Piece Marks]

─── TIME TRACKING RECORDS ───

[Time Entry] ────► Job + Station + Sequence + Lot + Task + Employee
│
Regular / OT / OT2 / Deduction Hours

─── PRODUCTION TRACKING RECORDS ───

[Prod Record] ────► Piece Mark + Station + Completed By + Date
## 5.2 Key Relationships to Remember
Time tracking records link to Jobs, Stations, Sequences, Lots, and Tasks—but NOT directly to Piece Marks.
Production tracking records link Piece Marks to Stations with completion timestamps.
To analyze time at the piece level, you must join time tracking (aggregated) with production tracking (per-piece) via shared dimensions (Job, Station, Sequence, Date).
Estimated hours live in the Estimating Job and are distributed by Labor Group.
Actual hours live in Time Tracking and are distributed by Station.
The Labor Group → Station mapping (defined at station setup) is the bridge for estimate-vs-actual comparison.

# 6. Mapping Concepts to Technical Interfaces
Now that you understand the conceptual model, let's discuss how this maps to technical surfaces and architectural approaches for your analytics work.
## 6.1 PowerFab Open API vs Database Direct Access
PowerFab exposes data through two primary channels:
**PowerFab Open API: **This is a .NET-based XML API that provides a data-access layer to the PowerFab database. The API uses request/response XML schemas (XSD files define the structure). You send HTTP POST requests with XML request documents and receive XML responses. The API is designed for real-time operational integrations: creating time tracking records, updating production status, querying job data. It's transactional and respects business logic.
**Database Direct Access: **PowerFab uses SQL Server. For analytics and reporting, direct database queries may be more practical than API calls, especially for historical analysis across many jobs. However, this requires understanding the database schema, which is not publicly documented in the same detail as the API. The database schema is considerably more complex than the conceptual model because it handles all the edge cases, audit trails, and system mechanics.
## 6.2 Recommended Architecture for Analytics
For your goals of historical reporting, labor cost analysis, and estimating accuracy feedback, I recommend a hybrid architecture:
**Extract-Transform-Load (ETL) from SQL Server: **Rather than querying the PowerFab database directly for each report, build a nightly ETL pipeline that extracts relevant data into an analytical data warehouse. This separates operational concerns from analytical workloads and lets you transform the complex transactional schema into simpler analytical tables.
**Analytical Data Model: **Create denormalized fact tables for time tracking and production tracking, with dimension tables for jobs, employees, stations, sequences. This star schema pattern makes queries fast and reports simple. For example: FACT_TimeTracking with columns for job_id, employee_id, station_id, sequence, lot, date, regular_hours, ot_hours, etc.
**Use API for Write Operations: **If you build custom data entry interfaces (mobile apps, kiosk screens), use the PowerFab API to write data. This ensures business rules are enforced and the transactional database stays consistent.
**Database Views for Integration: **Create read-only views in the PowerFab database (or a replica) that flatten the complex joins for common analytical queries. This provides a stable interface even if underlying table structures change in future PowerFab versions.
## 6.3 Key Tables to Investigate
While I cannot provide the exact schema (it's not publicly documented and varies by version), based on the conceptual model, you should look for tables related to:
Time tracking detail (the time entry records)
Production tracking / station history (piece mark completion records)
Production control jobs and bill of materials
Stations and routes
Estimating job labor (for estimate vs actual)
Labor groups and labor standards
Employees / users
Project schedule tasks
Consider working with Tekla/Trimble support or a certified implementation partner to get documentation on the database schema. If you have the PowerFab API license, the XSD files that define the request/response schemas will also give you insight into the data structures.

# 7. Summary and Recommended Next Steps
## 7.1 Key Takeaways
Time tracking in PowerFab records labor hours against Jobs, Stations, Sequences, Lots, and Tasks—not directly against individual piece marks.
Production tracking separately records piece-level completion status at each station.
These two data streams must be combined for piece-level labor analysis.
The Labor Group → Station mapping is essential for comparing estimated hours to actual hours.
Time tracking feeds into job costing, production scheduling, and estimating feedback loops.
For analytics, consider an ETL approach that separates operational data from analytical reporting.
## 7.2 Recommended Next Steps
**Get Database Access: **Work with your PowerFab administrator to get read access to a replica or backup of the production database for exploration.
**Map the Schema: **Use SQL Server tools to explore tables and relationships. Look for tables with names containing "TimeTrack", "Labor", "Station", "Production", "Schedule".
**Review API Documentation: **If you have PowerFab API access, review the XSD schemas to understand available endpoints and data structures.
**Build Prototype Queries: **Start with simple analytical queries: total hours by job, hours by station, estimate vs actual at job level.
**Design Your Analytical Model: **Based on your reporting requirements, design the star schema for your data warehouse.
**Engage Tekla/Trimble: **Consider reaching out to Tekla Partners Program for deeper integration support and schema documentation.
This conceptual foundation should serve you well as you move into the technical implementation phase. The key is to always map technical decisions back to the real-world workflows and business questions—that's what will make your analytics actually useful to shop floor managers and estimators.

| Approach | What Gets Recorded | Trade-offs |
| --- | --- | --- |
| Per-Shift | 8 hours to Job X, Station Y | Easy entry, low granularity. Can't track individual sequences. |
| Per-Station-Task | 4 hours welding Seq 3, 4 hours fitting Seq 4 | Good balance. Most common in practice. |
| Piece-Timer | Timer started/stopped per piece mark | High granularity, high burden. Time auto-distributed across batch. |


| Field | Description |
| --- | --- |
| Job | The production control job number |
| Employee | The PowerFab user who performed the work |
| Station | Which production station the work was performed at |
| Sequence | The sequence grouping (optional but common) |
| Lot | The lot within the sequence (optional) |
| Task | The project schedule task (links to Gantt chart) |
| Start Date/Time | When work began |
| End Date/Time | When work ended |
| Regular Hours | Hours at standard pay rate |
| OT Hours | Overtime hours (typically 1.5x rate) |
| OT2 Hours | Double overtime hours (typically 2x rate) |
| Deduction | Non-billable time (lunch, breaks) - not charged to job |
| Pay Category | Classification for payroll (configurable per job) |
