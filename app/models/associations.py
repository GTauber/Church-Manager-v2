"""
Association tables for many-to-many relationships.

Contains junction tables that link entities together.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ministry import Ministry


class UserMinistry(BaseModel):
    """
    Junction table managing many-to-many relationship between Users and Ministries.
    
    Tracks which users are members of which ministries and when they joined.
    
    Attributes:
        user_id: Foreign key to User
        ministry_id: Foreign key to Ministry
        joined_at: Timestamp when user joined the ministry
    
    Relationships:
        user: The user in this membership
        ministry: The ministry in this membership
    """
    
    __tablename__ = "user_ministry"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "ministry_id",
            name="unique_user_ministry_membership"
        ),
    )
    
    # Foreign keys
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User in this membership"
    )
    
    ministry_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("ministry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Ministry in this membership"
    )
    
    # Membership metadata
    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the user joined this ministry"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="user_ministries",
        lazy="selectin",
        doc="User in this membership"
    )
    
    ministry = relationship(
        "Ministry",
        back_populates="user_ministries",
        lazy="selectin",
        doc="Ministry in this membership"
    )
    
    def __repr__(self) -> str:
        """String representation of the UserMinistry."""
        user_name = self.user.full_name if self.user else "Unknown User"
        ministry_name = self.ministry.name if self.ministry else "Unknown Ministry"
        return (
            f"<UserMinistry(id={self.id}, user='{user_name}', "
            f"ministry='{ministry_name}', joined={self.joined_at.date()})>"
        )