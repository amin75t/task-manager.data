from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserDB(Base):
    """
    Database model for users

    Fields:
    - id: Primary key
    - phone: User's phone number (unique)
    - otp_code: Current OTP code (nullable)
    - otp_created_at: When OTP was created (nullable)
    - otp_verified: Whether OTP has been verified
    - created_at: Timestamp when user was created
    - updated_at: Timestamp when user was last updated
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone = Column(String, unique=True, nullable=False, index=True)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    otp_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone}')>"


class TaskDB(Base):
    """
    Database model for tasks

    Fields:
    - id: Primary key
    - title: Task title
    - description: Task description
    - user_id: ID of the user who created the task
    - time: Estimated time for the task (in minutes)
    - with_ai_flag: Whether the task was processed with AI
    - tags: List of tags (stored as JSON)
    - deadline: Task deadline
    - proprietary: Priority level (Urgent, High, Medium, Low)
    - created_at: Timestamp when task was created
    - updated_at: Timestamp when task was last updated
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    user_id = Column(Integer, nullable=False, index=True)
    time = Column(Integer, default=0)  # Time in minutes
    with_ai_flag = Column(Boolean, default=False)
    tags = Column(JSON, default=list)  # Store tags as JSON array
    deadline = Column(DateTime, nullable=True)
    proprietary = Column(String, default="Low")  # Priority level: Urgent, High, Medium, Low
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', user_id='{self.user_id}')>"
