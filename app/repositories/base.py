"""
Base repository pattern for database operations.

Provides generic async CRUD operations for all models.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import BaseModel

# TypeVar for generic model type
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common database operations.
    
    This class provides generic CRUD operations that can be used
    by all model-specific repositories.
    
    Attributes:
        model: The SQLAlchemy model class
        session: The async database session
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize the repository.
        
        Args:
            model: The SQLAlchemy model class
            session: The async database session
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            The created model instance
            
        Raises:
            IntegrityError: If unique constraint is violated
            SQLAlchemyError: For other database errors
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityError(
                f"Integrity constraint violation: {str(e.orig)}",
                params=None,
                orig=e.orig,
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
    
    async def get(
        self,
        id: UUID,
        load_relationships: bool = True
    ) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            id: The UUID of the record
            load_relationships: Whether to eagerly load relationships
            
        Returns:
            The model instance or None if not found
        """
        query = select(self.model).where(self.model.id == id)
        
        if load_relationships:
            # Eagerly load all relationships
            for relationship in self.model.__mapper__.relationships:
                query = query.options(selectinload(getattr(self.model, relationship.key)))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by(
        self,
        load_relationships: bool = True,
        **filters
    ) -> Optional[ModelType]:
        """
        Get a single record by field values.
        
        Args:
            load_relationships: Whether to eagerly load relationships
            **filters: Field values to filter by
            
        Returns:
            The first matching model instance or None
        """
        query = select(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(selectinload(getattr(self.model, relationship.key)))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        load_relationships: bool = False,
        order_by: Optional[str] = None,
        **filters
    ) -> List[ModelType]:
        """
        List records with optional filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            load_relationships: Whether to eagerly load relationships
            order_by: Field name to order by (prefix with '-' for DESC)
            **filters: Field values to filter by
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                field_name = order_by[1:]
                if hasattr(self.model, field_name):
                    query = query.order_by(getattr(self.model, field_name).desc())
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        else:
            # Default ordering by created_at desc
            if hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Load relationships if requested
        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(selectinload(getattr(self.model, relationship.key)))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(
        self,
        id: UUID,
        **kwargs
    ) -> Optional[ModelType]:
        """
        Update a record by ID.
        
        Args:
            id: The UUID of the record to update
            **kwargs: Field values to update
            
        Returns:
            The updated model instance or None if not found
            
        Raises:
            IntegrityError: If unique constraint is violated
            SQLAlchemyError: For other database errors
        """
        try:
            # Get the instance first
            instance = await self.get(id, load_relationships=False)
            if not instance:
                return None
            
            # Update fields
            for field, value in kwargs.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
            
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityError(
                f"Integrity constraint violation: {str(e.orig)}",
                params=None,
                orig=e.orig,
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: The UUID of the record to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            instance = await self.get(id, load_relationships=False)
            if not instance:
                return False
            
            await self.session.delete(instance)
            await self.session.flush()
            return True
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
    
    async def count(self, **filters) -> int:
        """
        Count records with optional filtering.
        
        Args:
            **filters: Field values to filter by
            
        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, **filters) -> bool:
        """
        Check if a record exists with given filters.
        
        Args:
            **filters: Field values to filter by
            
        Returns:
            True if at least one record exists
        """
        count = await self.count(**filters)
        return count > 0
    
    async def bulk_create(
        self,
        items: List[Dict[str, Any]]
    ) -> List[ModelType]:
        """
        Create multiple records in a single operation.
        
        Args:
            items: List of dictionaries with field values
            
        Returns:
            List of created model instances
            
        Raises:
            IntegrityError: If unique constraint is violated
            SQLAlchemyError: For other database errors
        """
        try:
            instances = [self.model(**item) for item in items]
            self.session.add_all(instances)
            await self.session.flush()
            
            # Refresh all instances
            for instance in instances:
                await self.session.refresh(instance)
            
            return instances
            
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityError(
                f"Integrity constraint violation: {str(e.orig)}",
                params=None,
                orig=e.orig,
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
    
    async def bulk_update(
        self,
        updates: List[Dict[str, Any]]
    ) -> int:
        """
        Update multiple records in a single operation.
        
        Args:
            updates: List of dictionaries with 'id' and fields to update
            
        Returns:
            Number of records updated
        """
        try:
            count = 0
            for update_data in updates:
                if 'id' in update_data:
                    id = update_data.pop('id')
                    instance = await self.update(id, **update_data)
                    if instance:
                        count += 1
            
            return count
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e