import sys
from datetime import datetime
from tabulate import tabulate
from app.logic import (
    register_member, update_member_profile, get_member_dashboard, schedule_pt_session,
    register_for_class, set_trainer_availability, get_trainer_schedule,
    add_new_room, create_group_class, get_member_name, get_trainer_name
)
from models.database import engine, Base, get_session, my_helper_sql_features
from models.schema import Room, GroupClass, Trainer, Member

# Initialize database with View, Trigger, Index
def init_db():
    print("Initializing Database...")
    Base.metadata.create_all(engine)
    my_helper_sql_features()  # Create View and Trigger
    print("Database Ready.\n")

# MY VISUALIZATION HELPERS
def print_header(text):
    print("\n" + "="*60)
    print(f"   {text.upper()}")
    print("="*60)

def print_table(data, headers):
    """Prints a list of lists/tuples as a formatted table."""
    if not data:
        print("\n(No data available)")
    else:
        print("\n" + tabulate(data, headers=headers, tablefmt="grid"))

def print_success(msg):
    print(f"\n[SUCCESS] {msg}")

def print_error(msg):
    print(f"\n[ERROR] {msg}")

# MENU FUNCTIONS 

def main_menu():
    init_db()
    while True:
        print_header("Health & Fitness Club Management System")
        print("1. MEMBER PORTAL")
        print("2. TRAINER PORTAL")
        print("3. ADMIN DASHBOARD")
        print("4. EXIT")
        
        choice = input("\nSelect an option (1-4): ").strip()

        if choice == '1': 
            member_menu()
        elif choice == '2': 
            trainer_menu()
        elif choice == '3': 
            admin_menu()
        elif choice == '4': 
            print("\nThank you for your patient going through my project!")
            sys.exit()
        else:
            print_error("Invalid choice. Please select 1-4.")

def member_menu():
    print_header("Member Portal")
    print("1. REGISTER NEW MEMBER")
    print("2. LOGIN (Existing Member)")
    print("3. BACK TO MAIN MENU")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        register_new_member()
    elif choice == '2':
        member_login()
    elif choice == '3':
        return
    else:
        print_error("Invalid choice.")

def register_new_member():
    """Member Registration - Requirement: User Registration"""
    print_header("New Member Registration")
    try:
        fname = input("First Name: ").strip()
        lname = input("Last Name: ").strip()
        email = input("Email: ").strip()
        pwd = input("Password: ").strip()
        dob_str = input("Date of Birth (YYYY-MM-DD): ").strip()
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        gender = input("Gender (M/F/Other): ").strip()
        
        mid = register_member(fname, lname, email, pwd, dob, gender)
        if mid:
            print_success(f"Registration complete! Your Member ID is: {mid}")
            input("\nPress Enter to continue to member dashboard...")
            member_dashboard_menu(mid, f"{fname} {lname}")
    except ValueError:
        print_error("Invalid date format. Please use YYYY-MM-DD")
    except Exception as e:
        print_error(f"Registration failed: {e}")

def member_login():
    """Member Login"""
    print_header("Member Login")
    try:
        mid_input = input("Enter your Member ID: ").strip()
        mid = int(mid_input)
        member_name = get_member_name(mid)
        
        if not member_name or member_name == "Unknown Member":
            print_error("Member ID not found. Please register first.")
            return
        
        print_success(f"Welcome back, {member_name}!")
        member_dashboard_menu(mid, member_name)
        
    except ValueError:
        print_error("Invalid ID format. Please enter a number.")

def member_dashboard_menu(mid, member_name):
    """Member's main operations menu"""
    while True:
        print_header(f"Member Dashboard - {member_name} (ID: {mid})")
        print("1. VIEW DASHBOARD (Health Stats & Progress)")
        print("2. UPDATE PROFILE (Email)")
        print("3. ADD HEALTH METRIC")
        print("4. ADD FITNESS GOAL")
        print("5. REGISTER FOR GROUP CLASS")
        print("6. SCHEDULE PERSONAL TRAINING SESSION")
        print("7. LOGOUT")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            # Dashboard Display
            get_member_dashboard(mid)
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            # Profile Management
            update_profile(mid)
            
        elif choice == '3':
            # Health History - Log multiple metric entries
            add_health_metric(mid)
            
        elif choice == '4':
            # Profile Management - fitness goals
            add_fitness_goal(mid)
            
        elif choice == '5':
            # Group Class Registration
            register_member_for_class(mid)
            
        elif choice == '6':
            # PT Session Scheduling
            book_pt_session(mid)
            
        elif choice == '7':
            print("\nLogging out...")
            break
        else:
            print_error("Invalid choice.")

def update_profile(mid):
    """Update member profile information"""
    print_header("Update Profile Information")
    email = input("New Email (press Enter to skip): ").strip() or None
    
    if email:
        update_member_profile(mid, new_email=email)
        print_success("Email updated successfully!")
    else:
        print("No changes made.")
    
    input("\nPress Enter to continue...")

def add_health_metric(mid):
    """Add health metric with timestamp - supports historical tracking"""
    print_header("Record Health Metric")
    print("Examples: Weight, Height, Heart Rate, Blood Pressure, Body Fat %")
    
    try:
        metric_type = input("\nMetric Type: ").strip()
        value = float(input("Value: "))
        unit = input("Unit (e.g., lbs, kg, bpm): ").strip()
        
        update_member_profile(mid, new_metric=(metric_type, value, unit))
        print_success(f"Health metric '{metric_type}' recorded!")
    except ValueError:
        print_error("Invalid value. Please enter a number.")
    
    input("\nPress Enter to continue...")

def add_fitness_goal(mid):
    """Add fitness goal with target"""
    print_header("Set Fitness Goal")
    print("Examples: Weight Loss, Muscle Gain, Endurance Improvement")
    
    try:
        goal_type = input("\nGoal Type: ").strip()
        target = float(input("Target Value: "))
        unit = input("Unit (e.g., lbs, kg, minutes): ").strip() or None
        deadline_str = input("Deadline (YYYY-MM-DD, or press Enter to skip): ").strip()
        
        deadline = None
        if deadline_str:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        
        update_member_profile(mid, new_goal=(goal_type, target, unit, deadline))
        print_success(f"Goal '{goal_type}' added successfully!")
    except ValueError:
        print_error("Invalid input format.")
    
    input("\nPress Enter to continue...")

def register_member_for_class(mid):
    """Register for group fitness class with capacity validation"""
    print_header("Group Class Registration")
    
    session = get_session()
    try:
        # Show upcoming classes
        upcoming_classes = session.query(GroupClass).filter(
            GroupClass.schedule_time >= datetime.now()
        ).order_by(GroupClass.schedule_time).all()
        
        if not upcoming_classes:
            print("\nNo upcoming classes available.")
            return
        
        class_data = []
        for gc in upcoming_classes:
            current_registrations = len(gc.registrations)
            class_data.append([
                gc.class_id,
                gc.title,
                gc.schedule_time.strftime("%Y-%m-%d %H:%M"),
                gc.duration_minutes,
                f"{current_registrations}/{gc.capacity}",
                gc.trainer.first_name + " " + gc.trainer.last_name,
                gc.room.room_name
            ])
        
        print("\n[UPCOMING CLASSES]")
        print_table(class_data, ["ID", "Title", "Date/Time", "Duration", "Registered/Capacity", "Trainer", "Room"])
        
        class_id = int(input("\nEnter Class ID to register (0 to cancel): ").strip())
        
        if class_id == 0:
            return
        
        register_for_class(mid, class_id)
        
    except ValueError:
        print_error("Invalid input.")
    except Exception as e:
        print_error(f"Registration failed: {e}")
    finally:
        session.close()
    
    input("\nPress Enter to continue...")

def book_pt_session(mid):
    """Schedule personal training session with trainer availability validation"""
    print_header("Schedule Personal Training Session")
    
    session = get_session()
    try:
        from models.schema import Availability
        
        # Show available trainers with their availability
        trainers = session.query(Trainer).all()
        if not trainers:
            print("\nNo trainers available.")
            return
        
        print("\n[TRAINERS & AVAILABILITY]")
        print("=" * 70)
        
        for t in trainers:
            print(f"\n  TRAINER ID: {t.trainer_id} | {t.first_name} {t.last_name} ({t.email})")
            
            # Get trainer's availability
            availabilities = session.query(Availability).filter(
                Availability.trainer_id == t.trainer_id
            ).order_by(Availability.day_of_week).all()
            
            if availabilities:
                print("  AVAILABLE TIMES:")
                for a in availabilities:
                    if a.is_recurring:
                        print(f"      - {a.day_of_week}s: {a.start_time.strftime('%H:%M')} - {a.end_time.strftime('%H:%M')}")
                    else:
                        print(f"      - {a.specific_date}: {a.start_time.strftime('%H:%M')} - {a.end_time.strftime('%H:%M')}")
            else:
                print("  [!] NO AVAILABILITY SET")
        
        print("\n" + "=" * 70)
        
        # Show available rooms
        rooms = session.query(Room).all()
        room_data = [[r.room_id, r.room_name, r.capacity] for r in rooms]
        print("\n[ROOMS]")
        print_table(room_data, ["ID", "Room Name", "Capacity"])
        
        tid = int(input("\nEnter Trainer ID: "))
        rid = int(input("Enter Room ID: "))
        date_str = input("Session Date (YYYY-MM-DD): ")
        session_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Show what day of week the selected date is
        day_name = session_date.strftime("%A")
        print(f"   -> {date_str} is a {day_name}")
        
        start = datetime.strptime(input("Start Time (HH:MM): "), "%H:%M").time()
        end = datetime.strptime(input("End Time (HH:MM): "), "%H:%M").time()
        
        schedule_pt_session(mid, tid, rid, session_date, start, end)
        
    except ValueError:
        print_error("Invalid input format.")
    except Exception as e:
        print_error(f"Booking failed: {e}")
    finally:
        session.close()
    
    input("\nPress Enter to continue...")

def trainer_menu():
    """Trainer Portal Entry"""
    print_header("Trainer Portal")
    try:
        tid_input = input("Enter your Trainer ID: ").strip()
        tid = int(tid_input)
        
        trainer_name = get_trainer_name(tid)
        if not trainer_name or trainer_name == "Unknown Trainer":
            print_error("Trainer ID not found.")
            return
        
        print_success(f"Welcome, {trainer_name}!")
        trainer_dashboard_menu(tid, trainer_name)
        
    except ValueError:
        print_error("Invalid ID format.")

def trainer_dashboard_menu(tid, trainer_name):
    """Trainer's main operations menu"""
    while True:
        print_header(f"Trainer Dashboard - {trainer_name} (ID: {tid})")
        print("1. SET/UPDATE AVAILABILITY")
        print("2. VIEW MY SCHEDULE")
        print("3. LOGOUT")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            # Requirement: Set Availability
            set_availability(tid)
            
        elif choice == '2':
            # Requirement: Schedule View
            get_trainer_schedule(tid)
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            print("\nLogging out...")
            break
        else:
            print_error("Invalid choice.")

def set_availability(tid):
    """Set trainer availability - prevents overlapping slots"""
    print_header("Set Availability")
    print("Define when you're available for sessions and classes")
    
    try:
        start = datetime.strptime(input("\nStart Time (HH:MM): "), "%H:%M").time()
        end = datetime.strptime(input("End Time (HH:MM): "), "%H:%M").time()
        
        if start >= end:
            print_error("End time must be after start time.")
            return
        
        is_rec = input("Is this recurring weekly? (y/n): ").strip().lower() == 'y'
        
        day = None
        date_val = None
        
        if is_rec:
            day = input("Day of Week (Monday-Sunday): ").strip().capitalize()
        else:
            date_str = input("Specific Date (YYYY-MM-DD): ").strip()
            date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        set_trainer_availability(tid, start, end, is_rec, day, date_val)
        
    except ValueError:
        print_error("Invalid format.")
    
    input("\nPress Enter to continue...")

def admin_menu():
    """Admin Portal Entry"""
    print_header("Admin Portal")
    try:
        aid_input = input("Enter your Admin ID: ").strip()
        aid = int(aid_input)
        
        # In production, verify admin exists in database
        print_success(f"Admin access granted (ID: {aid})")
        admin_dashboard_menu(aid)
        
    except ValueError:
        print_error("Invalid ID format.")

def admin_dashboard_menu(aid):
    """Admin's main operations menu"""
    while True:
        # Show current system stats
        session = get_session()
        room_count = session.query(Room).count()
        class_count = session.query(GroupClass).count()
        member_count = session.query(Member).count()
        trainer_count = session.query(Trainer).count()
        session.close()
        
        print_header(f"Admin Dashboard (ID: {aid})")
        print("[SYSTEM STATUS]")
        print(f"   Members: {member_count} | Trainers: {trainer_count}")
        print(f"   Rooms: {room_count} | Classes: {class_count}")
        print("-" * 60)
        
        print("1. ROOM MANAGEMENT")
        print("2. CLASS MANAGEMENT")
        print("3. VIEW ALL ROOMS")
        print("4. VIEW ALL CLASSES")
        print("5. LOGOUT")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            # Requirement: Room Booking
            manage_rooms(aid)
            
        elif choice == '2':
            # Requirement: Class Management
            manage_classes(aid)
            
        elif choice == '3':
            view_all_rooms()
            
        elif choice == '4':
            view_all_classes()
            
        elif choice == '5':
            print("\nLogging out...")
            break
        else:
            print_error("Invalid choice.")

def manage_rooms(aid):
    """Room management - add new rooms"""
    print_header("Room Management")
    print("1. ADD NEW ROOM")
    print("2. BACK")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        try:
            name = input("\nRoom Name: ").strip()
            cap = int(input("Capacity: "))
            
            if cap <= 0:
                print_error("Capacity must be positive.")
                return
            
            add_new_room(aid, name, cap)
        except ValueError:
            print_error("Invalid capacity.")
    
    input("\nPress Enter to continue...")

def manage_classes(aid):
    """Class management - create new group classes"""
    print_header("Class Management")
    print("1. CREATE NEW GROUP CLASS")
    print("2. BACK")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        session = get_session()
        try:
            # Show available trainers and rooms
            trainers = session.query(Trainer).all()
            rooms = session.query(Room).all()
            
            print("\n[AVAILABLE TRAINERS]")
            print_table([[t.trainer_id, f"{t.first_name} {t.last_name}"] for t in trainers], ["ID", "Name"])
            
            print("\n[AVAILABLE ROOMS]")
            print_table([[r.room_id, r.room_name, r.capacity] for r in rooms], ["ID", "Room", "Max Capacity"])
            
            title = input("\nClass Title: ").strip()
            desc = input("Description (optional): ").strip() or None
            tid = int(input("Trainer ID: "))
            rid = int(input("Room ID: "))
            time_str = input("Schedule (YYYY-MM-DD HH:MM): ")
            time_val = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            cap = int(input("Class Capacity: "))
            dur = int(input("Duration (minutes): "))
            
            create_group_class(aid, tid, rid, title, cap, time_val, dur, desc)
            
        except ValueError:
            print_error("Invalid input format.")
        except Exception as e:
            print_error(f"Failed to create class: {e}")
        finally:
            session.close()
    
    input("\nPress Enter to continue...")

def view_all_rooms():
    """Display all rooms in the system"""
    print_header("All Rooms")
    session = get_session()
    try:
        rooms = session.query(Room).all()
        room_data = [[r.room_id, r.room_name, r.capacity] for r in rooms]
        print_table(room_data, ["ID", "Room Name", "Capacity"])
    finally:
        session.close()
    
    input("\nPress Enter to continue...")

def view_all_classes():
    """Display all scheduled classes"""
    print_header("All Scheduled Classes")
    session = get_session()
    try:
        classes = session.query(GroupClass).order_by(GroupClass.schedule_time).all()
        class_data = []
        for c in classes:
            current = len(c.registrations)
            class_data.append([
                c.class_id,
                c.title,
                c.schedule_time.strftime("%Y-%m-%d %H:%M"),
                c.duration_minutes,
                f"{current}/{c.capacity}",
                c.trainer.first_name + " " + c.trainer.last_name,
                c.room.room_name
            ])
        
        print_table(class_data, ["ID", "Title", "Date/Time", "Duration", "Enrolled", "Trainer", "Room"])
    finally:
        session.close()
    
    input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()