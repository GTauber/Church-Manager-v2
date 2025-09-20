"""
User model for church members and volunteers.

Central entity representing all church members who can participate
in ministries and be assigned to schedules.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.ministry import Ministry
    from app.models.associations import UserMinistry
    from app.models.schedule import ScheduleAssignment


class User(BaseModel):
    """
    User model representing church members and volunteers.
    
    Attributes:
        username: Unique identifier for login
        email: Contact email address
        phone_number: WhatsApp phone number
        first_name: User's first name
        last_name: User's last name
        is_active: Whether the account is active
        is_available: General availability for scheduling
        date_joined: When the user registered
    
    Relationships:
        ministries: Ministries the user belongs to
        led_ministries: Ministries the user leads
        schedule_assignments: Schedule assignments for this user
    """
    
    __tablename__ = "user"
    
    # Authentication fields
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for login"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Contact email address"
    )
    
    phone_number = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="WhatsApp phone number (primary identifier)"
    )
    
    # Personal information
    first_name = Column(
        String(100),
        nullable=False,
        comment="User's first name"
    )
    
    last_name = Column(
        String(100),
        nullable=False,
        comment="User's last name"
    )
    
    # Status flags
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether the user account is active"
    )
    
    is_available = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="General availability for scheduling"
    )
    
    # Metadata
    date_joined = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the user registered"
    )
    
    # Relationships
    user_ministries = relationship(
        "UserMinistry",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Ministry memberships for this user"
    )
    
    led_ministries = relationship(
        "Ministry",
        back_populates="leader",
        foreign_keys="Ministry.leader_id",
        lazy="selectin",
        doc="Ministries this user leads"
    )
    
    schedule_assignments = relationship(
        "ScheduleAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Schedule assignments for this user"
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def ministries(self) -> List["Ministry"]:
        """Get list of ministries the user belongs to."""
        return [um.ministry for um in self.user_ministries if um.ministry]
    
    def __repr__(self) -> str:
        """String representation of the User."""
        return f"<User(id={self.id}, username='{self.username}', name='{self.full_name}')>"
    
    def can_be_scheduled(self) -> bool:
        """
        Check if user can be scheduled for assignments.
        
        Returns:
            True if user is active and available
        """
        return self.is_active and self.is_available