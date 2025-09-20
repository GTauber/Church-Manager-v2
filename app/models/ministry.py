"""
Ministry model for church service departments.

Represents different service areas or teams within the church
such as worship, sound, media, kids ministry, etc.
"""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.associations import UserMinistry
    from app.models.schedule import Schedule


class Ministry(BaseModel):
    """
    Ministry model representing church service departments.
    
    Attributes:
        name: Unique name of the ministry
        leader_id: Foreign key to User who leads this ministry
        is_active: Whether the ministry is currently active
    
    Relationships:
        leader: User who leads this ministry
        user_ministries: Users who are members of this ministry
        schedules: Schedules created for this ministry
    """
    
    __tablename__ = "ministry"
    
    # Basic information
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique name of the ministry"
    )
    
    # Leadership
    leader_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who leads this ministry (can be null initially)"
    )
    
    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether the ministry is currently active"
    )
    
    # Relationships
    leader = relationship(
        "User",
        back_populates="led_ministries",
        foreign_keys=[leader_id],
        lazy="selectin",
        doc="User who leads this ministry"
    )
    
    user_ministries = relationship(
        "UserMinistry",
        back_populates="ministry",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Users who are members of this ministry"
    )
    
    schedules = relationship(
        "Schedule",
        back_populates="ministry",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="Schedules for this ministry"
    )
    
    @property
    def members(self) -> List["User"]:
        """Get list of users who are members of this ministry."""
        return [um.user for um in self.user_ministries if um.user]
    
    @property
    def member_count(self) -> int:
        """Get the number of members in this ministry."""
        return len(self.user_ministries)
    
    def has_member(self, user_id: UUID) -> bool:
        """
        Check if a user is a member of this ministry.
        
        Args:
            user_id: UUID of the user to check
            
        Returns:
            True if the user is a member
        """
        return any(um.user_id == user_id for um in self.user_ministries)
    
    def can_create_schedule(self) -> bool:
        """
        Check if this ministry can create new schedules.
        
        Returns:
            True if ministry is active
        """
        return self.is_active
    
    def __repr__(self) -> str:
        """String representation of the Ministry."""
        leader_name = self.leader.full_name if self.leader else "No leader"
        return f"<Ministry(id={self.id}, name='{self.name}', leader='{leader_name}')>"