from models.database import get_session, Base, engine, my_helper_sql_features
from models.schema import (
    Member, Trainer, Admin, Room, Equipment, GroupClass, PTSession,
    Availability, HealthMetric, FitnessGoal, Billing, MaintenanceLog, ClassRegistration
)
from datetime import datetime, date, time

def seed_database():
    # 1. Reset Database (Drop all tables and recreate)
    print("Recreating tables...")
    
    # First, drop the VIEW and TRIGGER that depend on tables
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("DROP VIEW IF EXISTS v_member_dashboard_stats CASCADE"))
        conn.execute(text("DROP TRIGGER IF EXISTS trg_check_capacity ON class_registrations"))
        conn.execute(text("DROP FUNCTION IF EXISTS check_room_capacity() CASCADE"))
        conn.commit()
        print(" wecDropped existing views and triggers")
    
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # 2. Install Trigger and View
    my_helper_sql_features()
    
    session = get_session()
    try:
        print("Seeding data...")
        
        # ==========================================
        # USERS (Member, Trainer, Admin)
        # =========================================
        m1 = Member(first_name="Chris", last_name="Pham", email="chris@email.com", password="pass", gender="Male", dob=date(2005, 1, 1))
        m2 = Member(first_name="Tom", last_name="Pham", email="tom@email.com", password="pass", gender="Male", dob=date(2005, 5, 5))
        m3 = Member(first_name="Sarah", last_name="Johnson", email="sarah@email.com", password="pass", gender="Female", dob=date(1995, 3, 15))
        
        t1 = Trainer(first_name="Zack", last_name="Nguyen", email="zack@gym.com", password="pass")
        t2 = Trainer(first_name="Bao", last_name="Tran", email="bao@gym.com", password="pass")
        t3 = Trainer(first_name="Emily", last_name="Chen", email="emily@gym.com", password="pass")
        
        a1 = Admin(first_name="Leo", last_name="Zheng", email="leo@gym.com", password="pass")
        
        session.add_all([m1, m2, m3, t1, t2, t3, a1])
        session.commit()
        print("   Users created (3 members, 3 trainers, 1 admin)")

        # ==========================================
        # ROOMS & EQUIPMENT
        # ==========================================
        r1 = Room(room_name="Yoga Studio", capacity=20, admin_id=a1.admin_id)
        r2 = Room(room_name="Weight Room", capacity=50, admin_id=a1.admin_id)
        r3 = Room(room_name="Spin Room", capacity=15, admin_id=a1.admin_id)
        r4 = Room(room_name="PT Room A", capacity=5, admin_id=a1.admin_id)
        
        e1 = Equipment(name="Treadmill #1", status="Functional", admin_id=a1.admin_id, last_maintenance_date=date(2025, 10, 1))
        e2 = Equipment(name="Treadmill #2", status="Under Maintenance", admin_id=a1.admin_id, last_maintenance_date=date(2025, 9, 15))
        e3 = Equipment(name="Dumbbell Set", status="Functional", admin_id=a1.admin_id)
        e4 = Equipment(name="Spin Bike #1", status="Functional", admin_id=a1.admin_id)
        e5 = Equipment(name="Rowing Machine", status="Functional", admin_id=a1.admin_id)
        
        session.add_all([r1, r2, r3, r4, e1, e2, e3, e4, e5])
        session.commit()
        print("   Rooms and Equipment created")

        # =========================================
        # TRAINER AVAILABILITY
        # ==========================================
        # Trainer 1 (Zack) - Available Mon, Wed, Fri mornings
        av1 = Availability(trainer_id=t1.trainer_id, start_time=time(8, 0), end_time=time(12, 0), is_recurring=True, day_of_week="Monday")
        av2 = Availability(trainer_id=t1.trainer_id, start_time=time(8, 0), end_time=time(12, 0), is_recurring=True, day_of_week="Wednesday")
        av3 = Availability(trainer_id=t1.trainer_id, start_time=time(8, 0), end_time=time(12, 0), is_recurring=True, day_of_week="Friday")
        
        # Trainer 2 (Bao) - Available Tue, Thu afternoons and Sat all day
        av4 = Availability(trainer_id=t2.trainer_id, start_time=time(13, 0), end_time=time(20, 0), is_recurring=True, day_of_week="Tuesday")
        av5 = Availability(trainer_id=t2.trainer_id, start_time=time(13, 0), end_time=time(20, 0), is_recurring=True, day_of_week="Thursday")
        av6 = Availability(trainer_id=t2.trainer_id, start_time=time(9, 0), end_time=time(17, 0), is_recurring=True, day_of_week="Saturday")
        
        # Trainer 3 (Emily) - Available weekdays evenings
        av7 = Availability(trainer_id=t3.trainer_id, start_time=time(17, 0), end_time=time(21, 0), is_recurring=True, day_of_week="Monday")
        av8 = Availability(trainer_id=t3.trainer_id, start_time=time(17, 0), end_time=time(21, 0), is_recurring=True, day_of_week="Tuesday")
        av9 = Availability(trainer_id=t3.trainer_id, start_time=time(17, 0), end_time=time(21, 0), is_recurring=True, day_of_week="Wednesday")
        av10 = Availability(trainer_id=t3.trainer_id, start_time=time(17, 0), end_time=time(21, 0), is_recurring=True, day_of_week="Thursday")
        av11 = Availability(trainer_id=t3.trainer_id, start_time=time(17, 0), end_time=time(21, 0), is_recurring=True, day_of_week="Friday")
        
        session.add_all([av1, av2, av3, av4, av5, av6, av7, av8, av9, av10, av11])
        session.commit()
        print("   Trainer availability created")

        # ==========================================
        # HEALTH METRICS (Historical data for members)
        # ==========================================
        # Chris's weight tracking over time
        hm1 = HealthMetric(member_id=m1.member_id, type="Weight", value=180.5, unit="lbs", date_recorded=datetime(2025, 9, 1))
        hm2 = HealthMetric(member_id=m1.member_id, type="Weight", value=178.0, unit="lbs", date_recorded=datetime(2025, 10, 1))
        hm3 = HealthMetric(member_id=m1.member_id, type="Weight", value=175.5, unit="lbs", date_recorded=datetime(2025, 11, 1))
        hm4 = HealthMetric(member_id=m1.member_id, type="Heart Rate", value=72, unit="bpm", date_recorded=datetime(2025, 11, 1))
        hm5 = HealthMetric(member_id=m1.member_id, type="Body Fat", value=18.5, unit="%", date_recorded=datetime(2025, 11, 1))
        
        # Tom's metrics
        hm6 = HealthMetric(member_id=m2.member_id, type="Weight", value=165.0, unit="lbs", date_recorded=datetime(2025, 10, 15))
        hm7 = HealthMetric(member_id=m2.member_id, type="Height", value=5.9, unit="ft", date_recorded=datetime(2025, 10, 15))
        
        # Sarah's metrics
        hm8 = HealthMetric(member_id=m3.member_id, type="Weight", value=140.0, unit="lbs", date_recorded=datetime(2025, 11, 10))
        hm9 = HealthMetric(member_id=m3.member_id, type="Heart Rate", value=65, unit="bpm", date_recorded=datetime(2025, 11, 10))
        
        session.add_all([hm1, hm2, hm3, hm4, hm5, hm6, hm7, hm8, hm9])
        session.commit()
        print("    Health metrics created")

        # ==========================================
        # FITNESS GOALS
        # ==========================================
        fg1 = FitnessGoal(member_id=m1.member_id, type="Weight gain", target_value="170.0", unit="lbs", deadline=date(2025, 12, 31), achieved=False)
        fg2 = FitnessGoal(member_id=m1.member_id, type="Body Fat Reduction", target_value="15", unit="%", deadline=date(2026, 3, 1), achieved=False)
        fg3 = FitnessGoal(member_id=m2.member_id, type="Muscle Gain", target_value="15.0", unit="lbs", deadline=date(2026, 1, 15), achieved=False)
        fg4 = FitnessGoal(member_id=m3.member_id, type="Endurance", target_value="10.0", unit="km", deadline=date(2025, 12, 15), achieved=False)
        
        session.add_all([fg1, fg2, fg3, fg4])
        session.commit()
        print("   Fitness goals created")

        # =========================================
        # GROUP CLASSES
        # ==========================================
        c1 = GroupClass(title="Morning Yoga", description="Start your day with inner peace", 
                       schedule_time=datetime(2025, 12, 1, 9, 0), duration_minutes=60, 
                       capacity=20, trainer_id=t1.trainer_id, room_id=r1.room_id, admin_id=a1.admin_id)
        c2 = GroupClass(title="HIIT Blast", description="High intensity interval training", 
                       schedule_time=datetime(2025, 12, 2, 18, 0), duration_minutes=45, 
                       capacity=15, trainer_id=t3.trainer_id, room_id=r2.room_id, admin_id=a1.admin_id)
        c3 = GroupClass(title="Spin Class", description="Cardio cycling workout", 
                       schedule_time=datetime(2025, 12, 3, 17, 30), duration_minutes=50, 
                       capacity=15, trainer_id=t3.trainer_id, room_id=r3.room_id, admin_id=a1.admin_id)
        c4 = GroupClass(title="Weekend Warrior", description="Full body Saturday workout", 
                       schedule_time=datetime(2025, 12, 7, 10, 0), duration_minutes=90, 
                       capacity=25, trainer_id=t2.trainer_id, room_id=r2.room_id, admin_id=a1.admin_id)
        
        session.add_all([c1, c2, c3, c4])
        session.commit()
        print("   Group classes created")

        # ==========================================
        # CLASS REGISTRATIONS
        # ==========================================
        cr1 = ClassRegistration(member_id=m1.member_id, class_id=c1.class_id, status="Registered")
        cr2 = ClassRegistration(member_id=m2.member_id, class_id=c1.class_id, status="Registered")
        cr3 = ClassRegistration(member_id=m3.member_id, class_id=c2.class_id, status="Registered")
        cr4 = ClassRegistration(member_id=m1.member_id, class_id=c4.class_id, status="Registered")
        
        session.add_all([cr1, cr2, cr3, cr4])
        session.commit()
        print("   Class registrations created")

        # ==========================================
        # PT SESSIONS
        # ==========================================
        pt1 = PTSession(date=date(2025, 12, 2), start_time=time(14, 0), end_time=time(15, 0), 
                       status="Scheduled", member_id=m1.member_id, trainer_id=t2.trainer_id, room_id=r4.room_id)
        pt2 = PTSession(date=date(2025, 12, 4), start_time=time(14, 0), end_time=time(15, 0), 
                       status="Scheduled", member_id=m2.member_id, trainer_id=t2.trainer_id, room_id=r4.room_id)
        pt3 = PTSession(date=date(2025, 12, 3), start_time=time(18, 0), end_time=time(19, 0), 
                       status="Scheduled", member_id=m3.member_id, trainer_id=t3.trainer_id, room_id=r4.room_id)
        
        session.add_all([pt1, pt2, pt3])
        session.commit()
        print("   PT sessions created")

        # ==========================================
        # BILLING RECORDS
        # ==========================================
        b1 = Billing(member_id=m1.member_id, amount=99.99, service_type="Monthly Membership", 
                    status="Paid", payment_method="Credit Card", due_date=date(2025, 11, 1))
        b2 = Billing(member_id=m1.member_id, amount=50.00, service_type="PT Session", 
                    status="Paid", payment_method="Credit Card", due_date=date(2025, 11, 15))
        b3 = Billing(member_id=m2.member_id, amount=99.99, service_type="Monthly Membership", 
                    status="Pending", payment_method=None, due_date=date(2025, 12, 1))
        b4 = Billing(member_id=m3.member_id, amount=149.99, service_type="Quarterly Membership", 
                    status="Paid", payment_method="Debit Card", due_date=date(2025, 10, 1))
        
        session.add_all([b1, b2, b3, b4])
        session.commit()
        print("   Billing records created")

        # ==========================================
        # MAINTENANCE LOGS
        # ==========================================
        ml1 = MaintenanceLog(equipment_id=e2.equipment_id, admin_id=a1.admin_id, 
                            issue_description="Belt replacement needed", status="In Progress",
                            date_reported=datetime(2025, 11, 20))
        ml2 = MaintenanceLog(equipment_id=e1.equipment_id, admin_id=a1.admin_id, 
                            issue_description="Routine maintenance check", status="Completed",
                            date_reported=datetime(2025, 10, 1), date_resolved=datetime(2025, 10, 1))
        ml3 = MaintenanceLog(equipment_id=e4.equipment_id, admin_id=a1.admin_id, 
                            issue_description="Squeaky pedal reported by member", status="Pending",
                            date_reported=datetime(2025, 11, 25))
        
        session.add_all([ml1, ml2, ml3])
        session.commit()
        print("     Maintenance logs created")

        print("\n" + "="*50)
        print("Successfully seeded all data to the database")
        print("="*50)
        print("\nSummary:")
        print(f"   • Members: 3 (IDs: 1-3)")
        print(f"   • Trainers: 3 (IDs: 1-3)")
        print(f"   • Admins: 1 (ID: 1)")
        print(f"   • Rooms: 4")
        print(f"   • Equipment: 5")
        print(f"   • Trainer Availabilities: 11 slots")
        print(f"   • Group Classes: 4")
        print(f"   • Class Registrations: 4")
        print(f"   • PT Sessions: 3")
        print(f"   • Health Metrics: 9")
        print(f"   • Fitness Goals: 4")
        print(f"   • Billing Records: 4")
        print(f"   • Maintenance Logs: 3")
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()