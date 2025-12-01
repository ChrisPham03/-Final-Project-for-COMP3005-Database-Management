from sqlalchemy import Column, Integer, String, Float, Date, Time, ForeignKey, Boolean, DateTime, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base  


# 1. USER ENTITIES

class Member(Base):
    __tablename__ = 'members'
    member_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    gender = Column(String(10))
    dob = Column(Date)
    join_date = Column(DateTime, default=datetime.now)

    metrics = relationship("HealthMetric", back_populates="member", cascade="all, delete-orphan")
    goals = relationship("FitnessGoal", back_populates="member", cascade="all, delete-orphan")
    billings = relationship("Billing", back_populates="member", cascade="all, delete-orphan")
    pt_sessions = relationship("PTSession", back_populates="member")
    class_registrations = relationship("ClassRegistration", back_populates="member")

class Trainer(Base):
    __tablename__ = 'trainers'
    trainer_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    availabilities = relationship("Availability", back_populates="trainer", cascade="all, delete-orphan")
    classes_taught = relationship("GroupClass", back_populates="trainer")
    pt_sessions_led = relationship("PTSession", back_populates="trainer")

class Admin(Base):
    __tablename__ = 'admins'
    admin_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    rooms_managed = relationship("Room", back_populates="manager")
    equipment_maintained = relationship("Equipment", back_populates="manager")
    classes_managed = relationship("GroupClass", back_populates="manager")
    maintenance_tasks = relationship("MaintenanceLog", back_populates="admin")


# 2. CORE BUSINESS ENTITIES

class Room(Base):
    __tablename__ = 'rooms'
    room_id = Column(Integer, primary_key=True)
    room_name = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)

    admin_id = Column(Integer, ForeignKey('admins.admin_id'))
    manager = relationship("Admin", back_populates="rooms_managed")
    classes_hosted = relationship("GroupClass", back_populates="room")
    pt_sessions_hosted = relationship("PTSession", back_populates="room")

class GroupClass(Base):
    __tablename__ = 'group_classes'
    class_id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    schedule_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)

    trainer_id = Column(Integer, ForeignKey('trainers.trainer_id'))
    room_id = Column(Integer, ForeignKey('rooms.room_id'))
    admin_id = Column(Integer, ForeignKey('admins.admin_id'))

    trainer = relationship("Trainer", back_populates="classes_taught")
    room = relationship("Room", back_populates="classes_hosted")
    manager = relationship("Admin", back_populates="classes_managed")
    registrations = relationship("ClassRegistration", back_populates="group_class")

class PTSession(Base):
    __tablename__ = 'pt_sessions'
    session_id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), default='Scheduled')
    notes = Column(Text)

    member_id = Column(Integer, ForeignKey('members.member_id'))
    trainer_id = Column(Integer, ForeignKey('trainers.trainer_id'))
    room_id = Column(Integer, ForeignKey('rooms.room_id'))

    member = relationship("Member", back_populates="pt_sessions")
    trainer = relationship("Trainer", back_populates="pt_sessions_led")
    room = relationship("Room", back_populates="pt_sessions_hosted")
    
    __table_args__ = (
        # Creates an index to speed up conflict checking
        Index('idx_room_date_time', 'room_id', 'date', 'start_time'),
    )

# 3. WEAK & SUPPORTING ENTITIES

class HealthMetric(Base):
    __tablename__ = 'health_metrics'
    metric_id = Column(Integer, primary_key=True)
    date_recorded = Column(DateTime, default=datetime.now)
    type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    member_id = Column(Integer, ForeignKey('members.member_id'))
    member = relationship("Member", back_populates="metrics")

class FitnessGoal(Base):
    __tablename__ = 'fitness_goals'
    goal_id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    target_value = Column(Float, nullable=False)
    unit = Column(String(20))
    deadline = Column(Date)
    achieved = Column(Boolean, default=False)
    member_id = Column(Integer, ForeignKey('members.member_id'))
    member = relationship("Member", back_populates="goals")

class Availability(Base):
    __tablename__ = 'availabilities'
    availability_id = Column(Integer, primary_key=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_recurring = Column(Boolean, default=True) 
    day_of_week = Column(String(10))
    specific_date = Column(Date)
    trainer_id = Column(Integer, ForeignKey('trainers.trainer_id'))
    trainer = relationship("Trainer", back_populates="availabilities")

class ClassRegistration(Base):
    __tablename__ = 'class_registrations'
    registration_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.member_id'))
    class_id = Column(Integer, ForeignKey('group_classes.class_id'))
    registration_date = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='Registered')
    member = relationship("Member", back_populates="class_registrations")
    group_class = relationship("GroupClass", back_populates="registrations")
    
    
# OTHRER ENTITIES THAT IS NOT IN MY PROJECT SCOPE

class Equipment(Base):
    __tablename__ = 'equipment'
    equipment_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default='Functional')
    last_maintenance_date = Column(Date)

    admin_id = Column(Integer, ForeignKey('admins.admin_id'))
    manager = relationship("Admin", back_populates="equipment_maintained")
    maintenance_logs = relationship("MaintenanceLog", back_populates="equipment")
    
class Billing(Base):
    __tablename__ = 'billings'
    bill_id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date_issued = Column(DateTime, default=datetime.now)
    due_date = Column(Date)
    status = Column(String(20), default='Pending')
    service_type = Column(String(50))
    payment_method = Column(String(50))
    member_id = Column(Integer, ForeignKey('members.member_id'))
    member = relationship("Member", back_populates="billings")

class MaintenanceLog(Base):
    __tablename__ = 'maintenance_logs'
    log_id = Column(Integer, primary_key=True)
    issue_description = Column(Text, nullable=False)
    date_reported = Column(DateTime, default=datetime.now)
    date_resolved = Column(DateTime)
    status = Column(String(20), default='Pending')
    equipment_id = Column(Integer, ForeignKey('equipment.equipment_id'))
    admin_id = Column(Integer, ForeignKey('admins.admin_id'))
    equipment = relationship("Equipment", back_populates="maintenance_logs")
    admin = relationship("Admin", back_populates="maintenance_tasks")