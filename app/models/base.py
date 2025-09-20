"""
Base model class for all database entities.

Provides common fields and functionality for all models.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Abstract base class for all database models.
    
    Provides:
    - Automatic table naming based on class name
    - Common fields (id, created_at, updated_at)
    - Timestamp management
    """
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name in snake_case."""
        # Convert CamelCase to snake_case
        name = cls.__name__
        result = []
        for i, char in enumerate(name):
            if i > 0 and char.isupper():
                # Check if previous char is lowercase or next char is lowercase
                if (name[i-1].islower() or 
                    (i < len(name) - 1 and name[i+1].islower())):
                    result.append('_')
            result.append(char.lower())
        return ''.join(result)


class BaseModel(Base):
    """
    Base model with common fields for all entities.
    
    Attributes:
        id: UUID primary key, auto-generated
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
    """
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the record"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when the record was last updated"
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result