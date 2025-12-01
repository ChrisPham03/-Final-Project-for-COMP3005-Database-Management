# Health & Fitness Club Management System

## COMP 3005 - Database Management Systems - Final Project 

**Student Name:** Quang Minh Pham   
**Student ID:** 101300755  


---

## Project Overview

A database application for managing a health and fitness club. The system supports three user roles (Member, Trainer, Admin) and handles member registration, personal training sessions, group fitness classes, health tracking, and facility management.

**Technology Stack:**
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (Python)
- **Interface:** Command-Line Interface (CLI)

---

## Video Demonstration

**YouTube Link:** https://youtu.be/qwzh_keD5mA

---

## Features Implemented

### Member Functions (6 Operations)
| # | Operation | Description |
|---|-----------|-------------|
| 1 | User Registration | Create account with unique email validation |
| 2 | Profile Management | Update email address |
| 3 | Health History | Add time-stamped health metrics (weight, heart rate, etc.) |
| 4 | Dashboard Display | View stats, goals, upcoming sessions/classes (uses VIEW) |
| 5 | Group Class Registration | Register for classes with capacity validation (uses TRIGGER) |
| 6 | PT Session Scheduling | Book personal training with availability validation |

### Trainer Functions (2 Operations)
| # | Operation | Description |
|---|-----------|-------------|
| 7 | Set Availability | Define recurring or specific date availability |
| 8 | View Schedule | See upcoming PT sessions and classes |

### Admin Functions (2 Operations)
| # | Operation | Description |
|---|-----------|-------------|
| 9 | Room Management | Add new rooms with capacity |
| 10 | Class Management | Create group classes with room conflict detection |

---

## Database Schema

### Entities (9 Total)
1. **Member** - Club members with personal info
2. **Trainer** - Fitness trainers
3. **Admin** - System administrators
4. **Room** - Physical spaces with capacity
5. **GroupClass** - Scheduled fitness classes
6. **PTSession** - Personal training sessions
7. **HealthMetric** - Time-stamped health records (weak entity)
8. **FitnessGoal** - Member fitness targets
9. **Availability** - Trainer schedule slots

### Additional Entities (Not Implemented in Operations)
- **Equipment** - Gym equipment inventory
- **MaintenanceLog** - Equipment maintenance records
- **Billing** - Payment records

### Key Relationships
- Member ↔ GroupClass: **Many-to-Many** (via ClassRegistration)
- Member → HealthMetric: **1:N** with cascade delete (weak entity)
- Trainer → PTSession: **1:N**
- Room → GroupClass: **1:N** with total participation

---

## VIEW TRIGGER INDEX Features

### 1. VIEW - `v_member_dashboard_stats`
**Location:** `database.py` (lines 23-33)

```sql
CREATE OR REPLACE VIEW v_member_dashboard_stats AS
SELECT 
    m.member_id,
    m.first_name,
    m.last_name,
    COUNT(cr.registration_id) as total_classes_attended
FROM members m
LEFT JOIN class_registrations cr ON m.member_id = cr.member_id
GROUP BY m.member_id;
```

**Purpose:** Pre-aggregates member class participation for efficient dashboard queries.

### 2. TRIGGER - `trg_check_capacity`
**Location:** `database.py` (lines 35-72)

```sql
CREATE OR REPLACE FUNCTION check_room_capacity()
RETURNS TRIGGER AS $$
DECLARE
    current_count INTEGER;
    max_capacity INTEGER;
BEGIN
    SELECT capacity INTO max_capacity 
    FROM rooms 
    WHERE room_id = (SELECT room_id FROM group_classes WHERE class_id = NEW.class_id);

    SELECT COUNT(*) INTO current_count 
    FROM class_registrations 
    WHERE class_id = NEW.class_id;

    IF current_count >= max_capacity THEN
        RAISE EXCEPTION 'Room capacity exceeded for this class.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Purpose:** Automatically enforces room capacity when members register for classes.

### 3. INDEX - `idx_room_date_time`
**Location:** `schema.py` (lines 111-114)

```python
__table_args__ = (
    Index('idx_room_date_time', 'room_id', 'date', 'start_time'),
)
```

**Purpose:** Composite index to optimize PT session conflict-checking queries.

---

## Project Structure

```
project-root/
├── app/
│   ├── __init__.py
│   ├── main.py          # CLI interface
│   └── logic.py         # Business logic for all operations
├── models/
│   ├── __init__.py
│   ├── database.py      # DB connection, VIEW, TRIGGER
│   └── schema.py        # ORM entity classes, INDEX
├── docs/
│   └── ER.pdf           # ER diagram, mapping, normalization
├── seed_data.py         # Sample data population
└── README.md            # This file

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### 1. Install Dependencies (The tabulate lib, I used for better table visula in CLI )

```bash
pip install sqlalchemy psycopg2-binary tabulate
```

### 2. Create PostgreSQL Database

```sql
CREATE DATABASE fitness_club;
```

### 3. Configure Database Connection

Edit `database.py` and update the connection string:

```python
DATABASE_URL = "postgresql://username:password@localhost:5432/fitness_club"
```

### 4. Seed the Database

```bash
cd project-root
python3 seed_data.py
```

This will:
- Drop existing tables (if any)
- Create all tables
- Create VIEW and TRIGGER
- Populate sample data

### 5. Run the Application

```bash
python3 -m app.main
```

---

## Sample Login Credentials

After seeding, use these IDs to test:

| Role | ID | Name |
|------|----|------|
| Member | 1 | Alice Johnson |
| Member | 2 | Bob Smith |
| Member | 3 | Carol Williams |
| Trainer | 1 | Zack Nguyen |
| Trainer | 2 | Bao Tran |
| Trainer | 3 | Emily Chen |
| Admin | 1 | Admin User |

---

## Trainer Availability (Seeded)

| Trainer | Days | Hours |
|---------|------|-------|
| Zack Nguyen | Mon, Wed, Fri | 08:00 - 12:00 |
| Bao Tran | Tue, Thu | 13:00 - 20:00 |
| Bao Tran | Sat | 09:00 - 17:00 |
| Emily Chen | Mon - Fri | 17:00 - 21:00 |

---

## Usage Examples

### Register a New Member
```
Main Menu → 1 (Member Portal) → 1 (Register)
Enter: Name, Email, Password, DOB, Gender
```

### Book a PT Session
```
Member Dashboard → 6 (Schedule PT Session)
View trainer availability → Select trainer, room, date, time
```

### Register for Group Class
```
Member Dashboard → 5 (Register for Group Class)
View available classes → Enter Class ID
```

---

## Validation & Error Handling

The system validates:
- ✓ Unique email addresses
- ✓ Trainer availability before booking
- ✓ Room capacity (via TRIGGER)
- ✓ Room conflicts for classes and sessions
- ✓ Member double-booking prevention
- ✓ Trainer double-booking prevention
- ✓ Past class registration prevention

---

## ORM Bonus Implementation

This project uses **SQLAlchemy ORM** throughout:

1. **Entity Classes** - All tables defined as Python classes (`schema.py`)
2. **Relationships** - Properly mapped with `relationship()` and `ForeignKey`
3. **Cascade Deletes** - Weak entities use `cascade="all, delete-orphan"`
4. **No Raw SQL for CRUD** - All operations use ORM queries
5. **INDEX via ORM** - Defined in `__table_args__`

Raw SQL is only used for:
- Creating the VIEW (not supported by ORM)
- Creating the TRIGGER (not supported by ORM)
- Querying the VIEW in dashboard

---

## Normalization

All tables are normalized to **Third Normal Form (3NF)**:
- No repeating groups (1NF)
- No partial dependencies (2NF)
- No transitive dependencies (3NF)

See `ER.pdf` for my detailed normalization analysis.



