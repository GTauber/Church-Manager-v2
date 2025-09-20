"""
User repository for database operations.

Provides specialized methods for User model operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.associations import UserMinistry
from app.models.schedule import ScheduleAssignment, StatusCode
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations.
    
    Extends BaseRepository with User-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize UserRepository with User model."""
        super().__init__(User, session)
    
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """
        Get a user by phone number.
        
        Args:
            phone_number: The WhatsApp phone number
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by(phone_number=phone_number)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: The username
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by(username=username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: The email address
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by(email=email)
    
    async def search_users(
        self,
        query: str,
        limit: int = 10,
        only_active: bool = True
    ) -> List[User]:
        """
        Search users by name, username, email, or phone.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            only_active: Whether to filter only active users
            
        Returns:
            List of matching users
        """
        search_query = select(User).where(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
                User.phone_number.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
                func.concat(User.first_name, ' ', User.last_name).ilike(f"%{query}%")
            )
        )
        
        if only_active:
            search_query = search_query.where(User.is_active == True)
        
        search_query = search_query.limit(limit)
        
        result = await self.session.execute(search_query)
        return list(result.scalars().all())
    
    async def get_available_users(
        self,
        date: datetime = None,
        ministry_id: UUID = None
    ) -> List[User]:
        """
        Get users available for scheduling.
        
        Args:
            date: Optional date to check availability
            ministry_id: Optional ministry to filter by membership
            
        Returns:
            List of available users
        """
        query = select(User).where(
            and_(
                User.is_active == True,
                User.is_available == True
            )
        )
        
        # Filter by ministry membership if specified
        if ministry_id:
            query = query.join(UserMinistry).where(
                UserMinistry.ministry_id == ministry_id
            )
        
        # Exclude users already assigned on the specified date
        if date:
            # Subquery to get users with assignments on this date
            assigned_users = (
                select(ScheduleAssignment.user_id)
                .join(ScheduleAssignment.occurrence)
                .where(
                    and_(
                        ScheduleAssignment.occurrence.has(occurrence_date=date),
                        ScheduleAssignment.status_code != StatusCode.DECLINED.value
                    )
                )
            )
            
            query = query.where(~User.id.in_(assigned_users))
        
        # Eager load relationships
        query = query.options(
            selectinload(User.user_ministries).selectinload(UserMinistry.ministry)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_ministry_members(
        self,
        ministry_id: UUID,
        only_active: bool = True
    ) -> List[User]:
        """
        Get all members of a specific ministry.
        
        Args:
            ministry_id: The ministry ID
            only_active: Whether to filter only active users
            
        Returns:
            List of users in the ministry
        """
        query = (
            select(User)
            .join(UserMinistry)
            .where(UserMinistry.ministry_id == ministry_id)
        )
        
        if only_active:
            query = query.where(User.is_active == True)
        
        # Eager load relationships
        query = query.options(
            selectinload(User.user_ministries),
            selectinload(User.led_ministries)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def add_to_ministry(
        self,
        user_id: UUID,
        ministry_id: UUID
    ) -> bool:
        """
        Add a user to a ministry.
        
        Args:
            user_id: The user ID
            ministry_id: The ministry ID
            
        Returns:
            True if added successfully, False if already a member
        """
        # Check if already a member
        existing = await self.session.execute(
            select(UserMinistry).where(
                and_(
                    UserMinistry.user_id == user_id,
                    UserMinistry.ministry_id == ministry_id
                )
            )
        )
        
        if existing.scalar_one_or_none():
            return False
        
        # Add membership
        membership = UserMinistry(
            user_id=user_id,
            ministry_id=ministry_id
        )
        self.session.add(membership)
        await self.session.flush()
        
        return True
    
    async def remove_from_ministry(
        self,
        user_id: UUID,
        ministry_id: UUID
    ) -> bool:
        """
        Remove a user from a ministry.
        
        Args:
            user_id: The user ID
            ministry_id: The ministry ID
            
        Returns:
            True if removed successfully, False if not a member
        """
        result = await self.session.execute(
            select(UserMinistry).where(
                and_(
                    UserMinistry.user_id == user_id,
                    UserMinistry.ministry_id == ministry_id
                )
            )
        )
        
        membership = result.scalar_one_or_none()
        if not membership:
            return False
        
        await self.session.delete(membership)
        await self.session.flush()
        
        return True
    
    async def get_user_schedule(
        self,
        user_id: UUID,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[ScheduleAssignment]:
        """
        Get a user's schedule assignments.
        
        Args:
            user_id: The user ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of schedule assignments
        """
        query = (
            select(ScheduleAssignment)
            .where(ScheduleAssignment.user_id == user_id)
            .join(ScheduleAssignment.occurrence)
        )
        
        if start_date:
            query = query.where(
                ScheduleAssignment.occurrence.has(occurrence_date >= start_date)
            )
        
        if end_date:
            query = query.where(
                ScheduleAssignment.occurrence.has(occurrence_date <= end_date)
            )
        
        # Order by date and eager load relationships
        query = (
            query
            .order_by(ScheduleAssignment.occurrence.has(occurrence_date))
            .options(
                selectinload(ScheduleAssignment.occurrence)
                .selectinload(ScheduleAssignment.occurrence.schedule)
                .selectinload(ScheduleAssignment.occurrence.schedule.ministry)
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_availability(
        self,
        user_id: UUID,
        is_available: bool
    ) -> Optional[User]:
        """
        Update a user's availability status.
        
        Args:
            user_id: The user ID
            is_available: New availability status
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update(user_id, is_available=is_available)
    
    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: The user ID
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update(user_id, is_active=False, is_available=False)