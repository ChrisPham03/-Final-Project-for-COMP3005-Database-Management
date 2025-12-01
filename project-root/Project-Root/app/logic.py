from datetime import datetime, date
from sqlalchemy import func, text
from models.database import get_session
from models.schema import (
    Member, HealthMetric, FitnessGoal, PTSession, ClassRegistration, 
    GroupClass, Availability, Room, Trainer
)

# MEMBER OPERATIONS 

def register_member(first_name, last_name, email, password, dob, gender):
    """
    User Registration - Creates a new member with constraint on unique email.
    Returns member_id on success, None on failure.
    """
    session = get_session()
    try:
        # Check if email already exists
        existing = session.query(Member).filter(Member.email == email).first()
        if existing:
            print(f"[ERROR] Email '{email}' is already registered.")
            return None
        
        new_member = Member(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            dob=dob,
            gender=gender
        )
        session.add(new_member)
        session.commit()
        print(f"[SUCCESS] Member registered: {first_name} {last_name} (ID: {new_member.member_id})")
        return new_member.member_id
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Registration failed: {e}")
        return None
    finally:
        session.close()

def update_member_profile(member_id, new_email=None, new_metric=None, new_goal=None):
    """
    Profile Management - Update personal details|fitness goals|health metrics.
    new_metric format: (type, value, unit)
    new_goal format: (type, target_value, deadline)
    """
    session = get_session()
    try:
        member = session.query(Member).get(member_id)
        if not member:
            print("[ERROR] Member not found.")
            return False
        
        # Update email if provided
        if new_email:
            # Check if email is already taken
            existing = session.query(Member).filter(
                Member.email == new_email,
                Member.member_id != member_id
            ).first()
            if existing:
                print(f"[ERROR] Email '{new_email}' is already in use.")
                return False
            member.email = new_email
        
        # Add new health metric (Health History - time-stamped entries)
        if new_metric:
            metric = HealthMetric(
                member_id=member_id,
                type=new_metric[0],
                value=new_metric[1],
                unit=new_metric[2] if len(new_metric) > 2 else None,
                date_recorded=datetime.now()
            )
            session.add(metric)
        
        # Add new fitness goal
        if new_goal:
            goal = FitnessGoal(
                member_id=member_id,
                type=new_goal[0],
                target_value=new_goal[1],
                unit=new_goal[2] if len(new_goal) > 2 else None,
                deadline=new_goal[3] if len(new_goal) > 3 else None
            )
            session.add(goal)
        
        session.commit()
        print("[SUCCESS] Profile updated successfully.")
        return True
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to update profile: {e}")
        return False
    finally:
        session.close()

def get_member_dashboard(member_id):
    """
    Dashboard Display - Shows latest health stats, active goals, 
    past class count, and upcoming sessions.
    Uses the v_member_dashboard_stats view created in database.py
    """
    session = get_session()
    try:
        # Get member info
        member = session.query(Member).get(member_id)
        if not member:
            print("[ERROR] Member not found.")
            return
        
        print(f"\n{'='*60}")
        print(f"   MEMBER DASHBOARD - {member.first_name} {member.last_name}")
        print(f"{'='*60}")
        
        # Latest health metrics
        print("\n[LATEST HEALTH METRICS]")
        metrics = session.query(HealthMetric).filter(
            HealthMetric.member_id == member_id
        ).order_by(HealthMetric.date_recorded.desc()).all()
        
        if metrics:
            for m in metrics:
                unit_str = f" {m.unit}" if m.unit else ""
                print(f"   - {m.type}: {m.value}{unit_str} (recorded {m.date_recorded.strftime('%Y-%m-%d')})")
        else:
            print("   No metrics recorded yet.")
        
        # Active fitness goals
        print("\n[ACTIVE FITNESS GOALS]")
        goals = session.query(FitnessGoal).filter(
            FitnessGoal.member_id == member_id,
            FitnessGoal.achieved == False
        ).all()
        
        if goals:
            for g in goals:
                unit_str = f" {g.unit}" if g.unit else ""
                deadline_str = f" by {g.deadline}" if g.deadline else ""
                print(f"   - {g.type}: Target {g.target_value}{unit_str}{deadline_str}")
        else:
            print("   No active goals.")
        
        # Class participation count using the VIEW
        result = session.execute(
            text("SELECT total_classes_attended FROM v_member_dashboard_stats WHERE member_id = :mid"),
            {"mid": member_id}
        ).first()
        
        class_count = result[0] if result else 0
        print(f"\n[CLASS PARTICIPATION]")
        print(f"   Total Registered Classes: {class_count}")
        
        # Upcoming PT Sessions
        print("\n[UPCOMING PERSONAL TRAINING SESSIONS]")
        upcoming_sessions = session.query(PTSession).filter(
            PTSession.member_id == member_id,
            PTSession.date >= date.today(),
            PTSession.status == 'Scheduled'
        ).order_by(PTSession.date, PTSession.start_time).all()
        
        if upcoming_sessions:
            for s in upcoming_sessions:
                trainer = s.trainer
                print(f"   - {s.date} at {s.start_time} - {s.end_time}")
                print(f"     Trainer: {trainer.first_name} {trainer.last_name} | Room: {s.room.room_name}")
        else:
            print("   No upcoming sessions scheduled.")
        
        # Upcoming Group Classes
        print("\n[UPCOMING GROUP CLASSES]")
        upcoming_classes = session.query(ClassRegistration).join(GroupClass).filter(
            ClassRegistration.member_id == member_id,
            GroupClass.schedule_time >= datetime.now(),
            ClassRegistration.status == 'Registered'
        ).order_by(GroupClass.schedule_time).all()
        
        if upcoming_classes:
            for reg in upcoming_classes:
                gc = reg.group_class
                print(f"   - {gc.title}")
                print(f"     {gc.schedule_time.strftime('%Y-%m-%d %H:%M')} | {gc.duration_minutes} min | Room: {gc.room.room_name}")
        else:
            print("   No upcoming classes.")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"[ERROR] Failed to load dashboard: {e}")
    finally:
        session.close()

"This function has my index implementation for efficient conflict checking using the index defined in schema.py"
def schedule_pt_session(member_id, trainer_id, room_id, session_date, start_time, end_time):
    """
    PT Session Scheduling - Book or reschedule training with validation.
    Validates trainer availability and room conflicts.
    Uses the idx_room_date_time index for efficient conflict checking.
    """
    session = get_session()
    try:
        # Validate trainer exists
        trainer = session.query(Trainer).get(trainer_id)
        if not trainer:
            print("[ERROR] Trainer not found.")
            return False
        
        # Validate room exists
        room = session.query(Room).get(room_id)
        if not room:
            print("[ERROR] Room not found.")
            return False
        
        # Check for member conflicts (member can't be in two sessions at once)
        member_conflict = session.query(PTSession).filter(
            PTSession.member_id == member_id,
            PTSession.date == session_date,
            PTSession.start_time < end_time,
            PTSession.end_time > start_time
        ).first()
        
        if member_conflict:
            print(f"[ERROR] You already have a session booked during that time.")
            print(f"   Existing: {member_conflict.date} {member_conflict.start_time} - {member_conflict.end_time}")
            return False
        
        # Check for trainer conflicts (trainer can't be in two sessions at once)
        trainer_conflict = session.query(PTSession).filter(
            PTSession.trainer_id == trainer_id,
            PTSession.date == session_date,
            PTSession.start_time < end_time,
            PTSession.end_time > start_time
        ).first()
        
        if trainer_conflict:
            print(f"[ERROR] Trainer already has a session booked during that time.")
            print(f"   Existing: {trainer_conflict.date} {trainer_conflict.start_time} - {trainer_conflict.end_time}")
            return False
        
        # Check for room conflicts (uses idx_room_date_time index)
        conflict = session.query(PTSession).filter(
            PTSession.room_id == room_id,
            PTSession.date == session_date,
            PTSession.start_time < end_time,
            PTSession.end_time > start_time
        ).first()
        
        if conflict:
            print(f"[ERROR] Room '{room.room_name}' is already booked during that time.")
            return False
        
        # Check if trainer is available at the requested time
        day_name = session_date.strftime("%A")
        
        # Check for recurring availability on this day of week
        recurring_avail = session.query(Availability).filter(
            Availability.trainer_id == trainer_id,
            Availability.is_recurring == True,
            Availability.day_of_week == day_name,
            Availability.start_time <= start_time,
            Availability.end_time >= end_time
        ).first()
        
        # Check for specific date availability
        specific_avail = session.query(Availability).filter(
            Availability.trainer_id == trainer_id,
            Availability.is_recurring == False,
            Availability.specific_date == session_date,
            Availability.start_time <= start_time,
            Availability.end_time >= end_time
        ).first()
        
        if not recurring_avail and not specific_avail:
            all_avail = session.query(Availability).filter(
                Availability.trainer_id == trainer_id
            ).all()
            
            print(f"[ERROR] Trainer is not available at the requested time.")
            if all_avail:
                print(f"   Trainer's availability:")
                for a in all_avail:
                    if a.is_recurring:
                        print(f"   - {a.day_of_week}s: {a.start_time.strftime('%H:%M')} - {a.end_time.strftime('%H:%M')}")
                    else:
                        print(f"   - {a.specific_date}: {a.start_time.strftime('%H:%M')} - {a.end_time.strftime('%H:%M')}")
            else:
                print(f"   Trainer has no availability set. Please ask trainer to set their schedule.")
            return False
        
        # Create the session
        new_session = PTSession(
            member_id=member_id,
            trainer_id=trainer_id,
            room_id=room_id,
            date=session_date,
            start_time=start_time,
            end_time=end_time,
            status='Scheduled'
        )
        session.add(new_session)
        session.commit()
        
        print(f"[SUCCESS] PT Session booked successfully!")
        print(f"   Date: {session_date} | Time: {start_time} - {end_time}")
        print(f"   Trainer: {trainer.first_name} {trainer.last_name} | Room: {room.room_name}")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to book session: {e}")
        return False
    finally:
        session.close()

def register_for_class(member_id, class_id):
    """
    Group Class Registration - Register for scheduled classes if capacity permits.
    The database trigger 'check_room_capacity' enforces capacity constraints.
    """
    session = get_session()
    try:
        group_class = session.query(GroupClass).get(class_id)
        if not group_class:
            print("[ERROR] Class not found.")
            return False
        
        existing = session.query(ClassRegistration).filter(
            ClassRegistration.member_id == member_id,
            ClassRegistration.class_id == class_id
        ).first()
        
        if existing:
            print("[ERROR] You are already registered for this class.")
            return False
        
        if group_class.schedule_time < datetime.now():
            print("[ERROR] Cannot register for past classes.")
            return False
        
        registration = ClassRegistration(
            member_id=member_id,
            class_id=class_id,
            status='Registered'
        )
        session.add(registration)
        session.commit()
        
        print(f"[SUCCESS] Registered for '{group_class.title}'")
        print(f"   Scheduled: {group_class.schedule_time.strftime('%Y-%m-%d %H:%M')}")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Registration failed: {e}")
        return False
    finally:
        session.close()

# TRAINER OPERATIONS

def set_trainer_availability(trainer_id, start_time, end_time, is_recurring, day_of_week, specific_date):
    """
    Set Availability - Define time windows when available.
    Prevents overlapping slots for the same trainer.
    """
    session = get_session()
    try:
        trainer = session.query(Trainer).get(trainer_id)
        if not trainer:
            print("[ERROR] Trainer not found.")
            return False
        
        if is_recurring and day_of_week:
            overlap = session.query(Availability).filter(
                Availability.trainer_id == trainer_id,
                Availability.is_recurring == True,
                Availability.day_of_week == day_of_week,
                Availability.start_time < end_time,
                Availability.end_time > start_time
            ).first()
            
            if overlap:
                print(f"[ERROR] You already have availability set for {day_of_week} during that time.")
                return False
        
        elif specific_date:
            overlap = session.query(Availability).filter(
                Availability.trainer_id == trainer_id,
                Availability.specific_date == specific_date,
                Availability.start_time < end_time,
                Availability.end_time > start_time
            ).first()
            
            if overlap:
                print(f"[ERROR] You already have availability set for {specific_date} during that time.")
                return False
        
        new_avail = Availability(
            trainer_id=trainer_id,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring,
            day_of_week=day_of_week if is_recurring else None,
            specific_date=specific_date if not is_recurring else None
        )
        session.add(new_avail)
        session.commit()
        
        if is_recurring:
            print(f"[SUCCESS] Recurring availability set for {day_of_week}s: {start_time} - {end_time}")
        else:
            print(f"[SUCCESS] Availability set for {specific_date}: {start_time} - {end_time}")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to set availability: {e}")
        return False
    finally:
        session.close()

def get_trainer_schedule(trainer_id):
    """
    Schedule View - See assigned PT sessions and classes.
    """
    session = get_session()
    try:
        trainer = session.query(Trainer).get(trainer_id)
        if not trainer:
            print("[ERROR] Trainer not found.")
            return
        
        print(f"\n{'='*60}")
        print(f"   TRAINER SCHEDULE - {trainer.first_name} {trainer.last_name}")
        print(f"{'='*60}")
        
        # Upcoming PT Sessions
        print("\n[UPCOMING PERSONAL TRAINING SESSIONS]")
        sessions = session.query(PTSession).filter(
            PTSession.trainer_id == trainer_id,
            PTSession.date >= date.today()
        ).order_by(PTSession.date, PTSession.start_time).all()
        
        if sessions:
            for s in sessions:
                member = s.member
                print(f"   - {s.date} | {s.start_time} - {s.end_time}")
                print(f"     Client: {member.first_name} {member.last_name} | Room: {s.room.room_name}")
        else:
            print("   No upcoming PT sessions.")
        
        # Upcoming Group Classes
        print("\n[UPCOMING GROUP CLASSES]")
        classes = session.query(GroupClass).filter(
            GroupClass.trainer_id == trainer_id,
            GroupClass.schedule_time >= datetime.now()
        ).order_by(GroupClass.schedule_time).all()
        
        if classes:
            for c in classes:
                enrolled = len(c.registrations)
                print(f"   - {c.title}")
                print(f"     {c.schedule_time.strftime('%Y-%m-%d %H:%M')} | {c.duration_minutes} min")
                print(f"     Enrolled: {enrolled}/{c.capacity} | Room: {c.room.room_name}")
        else:
            print("   No upcoming classes.")
        
        # Current Availability
        print("\n[YOUR AVAILABILITY]")
        availabilities = session.query(Availability).filter(
            Availability.trainer_id == trainer_id
        ).all()
        
        if availabilities:
            for a in availabilities:
                if a.is_recurring:
                    print(f"   - {a.day_of_week}s: {a.start_time} - {a.end_time}")
                else:
                    print(f"   - {a.specific_date}: {a.start_time} - {a.end_time}")
        else:
            print("   No availability set.")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"[ERROR] Failed to load schedule: {e}")
    finally:
        session.close()

# ADMIN OPERATIONS 

def add_new_room(admin_id, room_name, capacity):
    """
    Room Booking - Assign rooms for sessions or classes.
    """
    session = get_session()
    try:
        new_room = Room(
            admin_id=admin_id,
            room_name=room_name,
            capacity=capacity
        )
        session.add(new_room)
        session.commit()
        
        print(f"[SUCCESS] Room '{room_name}' added successfully!")
        print(f"   Capacity: {capacity} | Room ID: {new_room.room_id}")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to add room: {e}")
        return False
    finally:
        session.close()

def create_group_class(admin_id, trainer_id, room_id, title, capacity, schedule_time, duration_minutes, description=None):
    """
    Class Management - Define new classes, assign trainers/rooms/time.
    """
    session = get_session()
    try:
        trainer = session.query(Trainer).get(trainer_id)
        if not trainer:
            print("[ERROR] Trainer not found.")
            return False
        
        room = session.query(Room).get(room_id)
        if not room:
            print("[ERROR] Room not found.")
            return False
        
        if capacity > room.capacity:
            print(f"[ERROR] Class capacity ({capacity}) exceeds room capacity ({room.capacity}).")
            print(f"   Maximum allowed: {room.capacity}")
            return False
                
        from datetime import timedelta
        new_end_time = schedule_time + timedelta(minutes=duration_minutes)
        
        existing_classes = session.query(GroupClass).filter(
            GroupClass.room_id == room_id
        ).all()
        
        for existing in existing_classes:
            existing_end = existing.schedule_time + timedelta(minutes=existing.duration_minutes)
            if existing.schedule_time < new_end_time and existing_end > schedule_time:
                print(f"[ERROR] Room '{room.room_name}' is already booked during that time.")
                print(f"   Conflict with: '{existing.title}' ({existing.schedule_time.strftime('%H:%M')} - {existing_end.strftime('%H:%M')})")
                return False
        
        new_class = GroupClass(
            admin_id=admin_id,
            trainer_id=trainer_id,
            room_id=room_id,
            title=title,
            description=description,
            schedule_time=schedule_time,
            duration_minutes=duration_minutes,
            capacity=capacity
        )
        session.add(new_class)
        session.commit()
        
        print(f"[SUCCESS] Class '{title}' created successfully!")
        print(f"   Trainer: {trainer.first_name} {trainer.last_name}")
        print(f"   Room: {room.room_name} | Capacity: {capacity}")
        print(f"   Schedule: {schedule_time.strftime('%Y-%m-%d %H:%M')} | Duration: {duration_minutes} min")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to create class: {e}")
        return False
    finally:
        session.close()

# HELPER FUNCTIONS

def get_member_name(member_id):
    """Get member's full name by ID"""
    session = get_session()
    try:
        member = session.query(Member).get(member_id)
        if member:
            return f"{member.first_name} {member.last_name}"
        return "Unknown Member"
    finally:
        session.close()

def get_trainer_name(trainer_id):
    """Get trainer's full name by ID"""
    session = get_session()
    try:
        trainer = session.query(Trainer).get(trainer_id)
        if trainer:
            return f"{trainer.first_name} {trainer.last_name}"
        return "Unknown Trainer"
    finally:
        session.close()