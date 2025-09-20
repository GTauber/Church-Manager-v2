"""
Schedule models for managing church service schedules.

Includes Schedule (template), ScheduleOccurrence (specific dates),
and ScheduleAssignment (user-role assignments).
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, validates

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ministry import Ministry


class RoleCode(str, Enum):
    """Enumeration of possible role codes for assignments."""
    
    WORSHIP_LEAD = "WORSHIP_LEAD"
    SOUND_TECH = "SOUND_TECH"
    MEDIA = "MEDIA"
    KIDS_TEACHER = "KIDS_TEACHER"
    GREETER = "GREETER"
    PRAYER = "PRAYER"
    COMMUNION = "COMMUNION"
    OFFERING = "OFFERING"
    SECURITY = "SECURITY"
    CLEANING = "CLEANING"
    OTHER = "OTHER"


class StatusCode(str, Enum):
    """Enumeration of possible status codes for assignments."""
    
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class Schedule(BaseModel):
    """
    Schedule model representing a schedule template for a period.
    
    For example: "December 2024 Worship Schedule"
    
    Attributes:
        ministry_id: Foreign key to the Ministry this schedule belongs to
        title: Name of the schedule
        notes: Additional information about the schedule
        start_date: Start date of the schedule period
        end_date: End date of the schedule period
    
    Relationships:
        ministry: The ministry this schedule belongs to
        occurrences: Specific dates within this schedule
    """
    
    __tablename__ = "schedule"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="check_schedule_dates"
        ),
    )
    
    # Foreign keys
    ministry_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("ministry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Ministry this schedule belongs to"
    )
    
    # Schedule information
    title = Column(
        String(200),
        nullable=False,
        comment="Name of the schedule"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Additional information about the schedule"
    )
    
    # Date range
    start_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Start date of the schedule period"
    )
    
    end_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="End date of the schedule period"
    )
    
    # Relationships
    ministry = relationship(
        "Ministry",
        back_populates="schedules",
        lazy="selectin",
        doc="Ministry this schedule belongs to"
    )
    
    occurrences = relationship(
        "ScheduleOccurrence",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ScheduleOccurrence.occurrence_date",
        doc="Specific dates within this schedule"
    )
    
    @validates("end_date")
    def validate_end_date(self, key: str, value: date) -> date:
        """Validate that end_date is after start_date."""
        if self.start_date and value < self.start_date:
            raise ValueError("End date must be after or equal to start date")
        return value
    
    @property
    def occurrence_count(self) -> int:
        """Get the number of occurrences in this schedule."""
        return len(self.occurrences)
    
    def __repr__(self) -> str:
        """String representation of the Schedule."""
        return (
            f"<Schedule(id={self.id}, title='{self.title}', "
            f"dates={self.start_date} to {self.end_date})>"
        )


class ScheduleOccurrence(BaseModel):
    """
    ScheduleOccurrence model representing specific dates within a schedule.
    
    For example: "Sunday, December 10, 2024"
    
    Attributes:
        schedule_id: Foreign key to the Schedule this belongs to
        occurrence_date: The specific date of this occurrence
        day_of_week: Day name (auto-calculated from date)
        notes: Occurrence-specific notes
    
    Relationships:
        schedule: The schedule this occurrence belongs to
        assignments: User assignments for this occurrence
    """
    
    __tablename__ = "schedule_occurrence"
    
    # Foreign keys
    schedule_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("schedule.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Schedule this occurrence belongs to"
    )
    
    # Occurrence information
    occurrence_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Specific date of this occurrence"
    )
    
    day_of_week = Column(
        String(10),
        nullable=False,
        comment="Day name (e.g., 'Sunday')"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Occurrence-specific notes"
    )
    
    # Relationships
    schedule = relationship(
        "Schedule",
        back_populates="occurrences",
        lazy="selectin",
        doc="Schedule this occurrence belongs to"
    )
    
    assignments = relationship(
        "ScheduleAssignment",
        back_populates="occurrence",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ScheduleAssignment.role_code",
        doc="User assignments for this occurrence"
    )
    
    @validates("occurrence_date")
    def validate_occurrence_date(self, key: str, value: date) -> date:
        """
        Validate that occurrence_date is within schedule range
        and set day_of_week.
        """
        if self.schedule:
            if value < self.schedule.start_date or value > self.schedule.end_date:
                raise ValueError(
                    f"Occurrence date must be between {self.schedule.start_date} "
                    f"and {self.schedule.end_date}"
                )
        
        # Set day of week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                "Friday", "Saturday", "Sunday"]
        self.day_of_week = days[value.weekday()]
        
        return value
    
    @property
    def assignment_count(self) -> int:
        """Get the number of assignments for this occurrence."""
        return len(self.assignments)
    
    def get_assignments_by_status(self, status: StatusCode) -> List["ScheduleAssignment"]:
        """Get assignments filtered by status."""
        return [a for a in self.assignments if a.status_code == status.value]
    
    def __repr__(self) -> str:
        """String representation of the ScheduleOccurrence."""
        return (
            f"<ScheduleOccurrence(id={self.id}, "
            f"date={self.occurrence_date} ({self.day_of_week}))>"
        )


class ScheduleAssignment(BaseModel):
    """
    ScheduleAssignment model linking users to specific roles on specific dates.
    
    Attributes:
        occurrence_id: Foreign key to the ScheduleOccurrence
        user_id: Foreign key to the User being assigned
        role_code: Role identifier (e.g., WORSHIP_LEAD, SOUND_TECH)
        status_code: Assignment status (e.g., ASSIGNED, CONFIRMED)
        notes: Assignment-specific notes
    
    Relationships:
        occurrence: The schedule occurrence this assignment is for
        user: The user assigned to this role
    """
    
    __tablename__ = "schedule_assignment"
    __table_args__ = (
        UniqueConstraint(
            "occurrence_id", "user_id", "role_code",
            name="unique_user_role_per_occurrence"
        ),
    )
    
    # Foreign keys
    occurrence_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("schedule_occurrence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Schedule occurrence this assignment is for"
    )
    
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User assigned to this role"
    )
    
    # Assignment information
    role_code = Column(
        String(50),
        nullable=False,
        comment="Role identifier (e.g., WORSHIP_LEAD)"
    )
    
    status_code = Column(
        String(20),
        nullable=False,
        default=StatusCode.ASSIGNED.value,
        index=True,
        comment="Assignment status (e.g., ASSIGNED, CONFIRMED)"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Assignment-specific notes"
    )
    
    # Relationships
    occurrence = relationship(
        "ScheduleOccurrence",
        back_populates="assignments",
        lazy="selectin",
        doc="Schedule occurrence this assignment is for"
    )
    
    user = relationship(
        "User",
        back_populates="schedule_assignments",
        lazy="selectin",
        doc="User assigned to this role"
    )
    
    @validates("role_code")
    def validate_role_code(self, key: str, value: str) -> str:
        """Validate role code is valid."""
        valid_roles = [role.value for role in RoleCode]
        if value not in valid_roles:
            raise ValueError(f"Invalid role code: {value}. Must be one of {valid_roles}")
        return value
    
    @validates("status_code")
    def validate_status_code(self, key: str, value: str) -> str:
        """Validate status code is valid."""
        valid_statuses = [status.value for status in StatusCode]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status code: {value}. Must be one of {valid_statuses}")
        return value
    
    def can_transition_to(self, new_status: StatusCode) -> bool:
        """
        Check if assignment can transition to new status.
        
        Business rules for status transitions:
        - ASSIGNED -> CONFIRMED, DECLINED
        - CONFIRMED -> COMPLETED, NO_SHOW
        - DECLINED -> ASSIGNED (reassignment)
        - COMPLETED -> (no transitions)
        - NO_SHOW -> (no transitions)
        """
        current = self.status_code
        new = new_status.value
        
        transitions = {
            StatusCode.ASSIGNED.value: [StatusCode.CONFIRMED.value, StatusCode.DECLINED.value],
            StatusCode.CONFIRMED.value: [StatusCode.COMPLETED.value, StatusCode.NO_SHOW.value],
            StatusCode.DECLINED.value: [StatusCode.ASSIGNED.value],
            StatusCode.COMPLETED.value: [],
            StatusCode.NO_SHOW.value: [],
        }
        
        return new in transitions.get(current, [])
    
    def __repr__(self) -> str:
        """String representation of the ScheduleAssignment."""
        user_name = self.user.full_name if self.user else "Unknown"
        return (
            f"<ScheduleAssignment(id={self.id}, user='{user_name}', "
            f"role={self.role_code}, status={self.status_code})>"
        )