from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

 # Loads the .env file and assigns environment variables
load_dotenv() 
database_url = os.getenv("DATABASE_URL")



engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    return SessionLocal()

# Create SQL Objects 
def my_helper_sql_features():
    """
    Creates the required View and Trigger using raw SQL.
    Must be run AFTER Base.metadata.create_all(engine).
    """
    with engine.connect() as conn:
        # 1. CREATE VIEW: Member Dashboard Stats
        # Aggregates class counts for the dashboard requirement 
        conn.execute(text("""
            CREATE OR REPLACE VIEW v_member_dashboard_stats AS
            SELECT 
                m.member_id,
                m.first_name,
                m.last_name,
                COUNT(cr.registration_id) as total_classes_attended
            FROM members m
            LEFT JOIN class_registrations cr ON m.member_id = cr.member_id
            GROUP BY m.member_id;
        """))

        # 2. CREATE TRIGGER FUNCTION: Enforce Room Capacity
        # "ensuring that room capacities are not exceeded" 
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION check_room_capacity()
            RETURNS TRIGGER AS $$
            DECLARE
                current_count INTEGER;
                max_capacity INTEGER;
            BEGIN
                -- Get the room capacity
                SELECT capacity INTO max_capacity 
                FROM rooms 
                WHERE room_id = (SELECT room_id FROM group_classes WHERE class_id = NEW.class_id);

                -- Get current registrations for this class
                SELECT COUNT(*) INTO current_count 
                FROM class_registrations 
                WHERE class_id = NEW.class_id;

                IF current_count >= max_capacity THEN
                    RAISE EXCEPTION 'Room capacity exceeded for this class.';
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        # 3. CREATE TRIGGER: Bind function to table
        # Checks before a member registers for a class
        conn.execute(text("""
            DROP TRIGGER IF EXISTS trg_check_capacity ON class_registrations;
            
            CREATE TRIGGER trg_check_capacity
            BEFORE INSERT ON class_registrations
            FOR EACH ROW
            EXECUTE FUNCTION check_room_capacity();
        """))
        
        conn.commit()
        print("[SUCCESS] SQL View and Trigger created successfully.")