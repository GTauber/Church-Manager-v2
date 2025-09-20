"""
Ministry repository for database operations.

Provides specialized methods for Ministry model operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ministry import Ministry
from app.models.user import User
from app.models.associations import UserMinistry
from app.models.schedule import Schedule
from app.repositories.base import BaseRepository


class MinistryRepository(BaseRepository[Ministry]):
    """
    Repository for Ministry model operations.
    
    Extends BaseRepository with Ministry-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize MinistryRepository with Ministry model."""
        super().__init__(Ministry, session)
    
    async def get_by_name(self, name: str) -> Optional[Ministry]:
        """
        Get a ministry by name.
        
        Args:
            name: The ministry name
            
        Returns:
            Ministry instance or None if not found
        """
        return await self.get_by(name=name)
    
    async def get_active_ministries(self) -> List[Ministry]:
        """
        Get all active ministries.
        
        Returns:
            List of active ministries
        """
        query = (
            select(Ministry)
            .where(Ministry.is_active == True)
            .options(
                selectinload(Ministry.leader),
                selectinload(Ministry.user_ministries).selectinload(UserMinistry.user)
            )
            .order_by(Ministry.name)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_ministries(
        self,
        user_id: UUID,
        only_active: bool = True
    ) -> List[Ministry]:
        """
        Get all ministries a user belongs to.
        
        Args:
            user_id: The user ID
            only_active: Whether to filter only active ministries
            
        Returns:
            List of ministries the user belongs to
        """
        query = (
            select(Ministry)
            .join(UserMinistry)
            .where(UserMinistry.user_id == user_id)
        )
        
        if only_active:
            query = query.where(Ministry.is_active == True)
        
        query = query.options(
            selectinload(Ministry.leader),
            selectinload(Ministry.user_ministries)
        ).order_by(Ministry.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_led_ministries(
        self,
        leader_id: UUID,
        only_active: bool = True
    ) -> List[Ministry]:
        """
        Get all ministries led by a specific user.
        
        Args:
            leader_id: The leader's user ID
            only_active: Whether to filter only active ministries
            
        Returns:
            List of ministries led by the user
        """
        query = select(Ministry).where(Ministry.leader_id == leader_id)
        
        if only_active:
            query = query.where(Ministry.is_active == True)
        
        query = query.options(
            selectinload(Ministry.user_ministries).selectinload(UserMinistry.user)
        ).order_by(Ministry.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def set_leader(
        self,
        ministry_id: UUID,
        leader_id: UUID
    ) -> Optional[Ministry]:
        """
        Set or change the leader of a ministry.
        
        Args:
            ministry_id: The ministry ID
            leader_id: The new leader's user ID
            
        Returns:
            Updated ministry instance or None if not found
        """
        # Verify the user exists
        user_result = await self.session.execute(
            select(User).where(User.id == leader_id)
        )
        if not user_result.scalar_one_or_none():
            raise ValueError(f"User with ID {leader_id} not found")
        
        # Ensure the leader is a member of the ministry
        await self.add_member(ministry_id, leader_id)
        
        # Update the leader
        return await self.update(ministry_id, leader_id=leader_id)
    
    async def add_member(
        self,
        ministry_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Add a member to a ministry.
        
        Args:
            ministry_id: The ministry ID
            user_id: The user ID to add
            
        Returns:
            True if added successfully, False if already a member
        """
        # Check if already a member
        existing = await self.session.execute(
            select(UserMinistry).where(
                and_(
                    UserMinistry.ministry_id == ministry_id,
                    UserMinistry.user_id == user_id
                )
            )
        )
        
        if existing.scalar_one_or_none():
            return False
        
        # Add membership
        membership = UserMinistry(
            ministry_id=ministry_id,
            user_id=user_id
        )
        self.session.add(membership)
        await self.session.flush()
        
        return True
    
    async def remove_member(
        self,
        ministry_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove a member from a ministry.
        
        Args:
            ministry_id: The ministry ID
            user_id: The user ID to remove
            
        Returns:
            True if removed successfully, False if not a member
        """
        # Check if user is the leader
        ministry = await self.get(ministry_id)
        if ministry and ministry.leader_id == user_id:
            # Remove leadership first
            await self.update(ministry_id, leader_id=None)
        
        # Remove membership
        result = await self.session.execute(
            select(UserMinistry).where(
                and_(
                    UserMinistry.ministry_id == ministry_id,
                    UserMinistry.user_id == user_id
                )
            )
        )
        
        membership = result.scalar_one_or_none()
        if not membership:
            return False
        
        await self.session.delete(membership)
        await self.session.flush()
        
        return True
    
    async def get_ministry_schedules(
        self,
        ministry_id: UUID,
        limit: int = 10
    ) -> List[Schedule]:
        """
        Get schedules for a ministry.
        
        Args:
            ministry_id: The ministry ID
            limit: Maximum number of schedules to return
            
        Returns:
            List of schedules for the ministry
        """
        query = (
            select(Schedule)
            .where(Schedule.ministry_id == ministry_id)
            .options(
                selectinload(Schedule.occurrences)
            )
            .order_by(Schedule.start_date.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_member_count(self, ministry_id: UUID) -> int:
        """
        Get the number of members in a ministry.
        
        Args:
            ministry_id: The ministry ID
            
        Returns:
            Number of members
        """
        query = (
            select(func.count())
            .select_from(UserMinistry)
            .where(UserMinistry.ministry_id == ministry_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def deactivate_ministry(
        self,
        ministry_id: UUID
    ) -> Optional[Ministry]:
        """
        Deactivate a ministry.
        
        Args:
            ministry_id: The ministry ID
            
        Returns:
            Updated ministry instance or None if not found
        """
        return await self.update(ministry_id, is_active=False)
    
    async def reactivate_ministry(
        self,
        ministry_id: UUID
    ) -> Optional[Ministry]:
        """
        Reactivate a previously deactivated ministry.
        
        Args:
            ministry_id: The ministry ID
            
        Returns:
            Updated ministry instance or None if not found
        """
        return await self.update(ministry_id, is_active=True)
    
    async def search_ministries(
        self,
        query: str,
        only_active: bool = True
    ) -> List[Ministry]:
        """
        Search ministries by name.
        
        Args:
            query: Search query string
            only_active: Whether to filter only active ministries
            
        Returns:
            List of matching ministries
        """
        search_query = select(Ministry).where(
            Ministry.name.ilike(f"%{query}%")
        )
        
        if only_active:
            search_query = search_query.where(Ministry.is_active == True)
        
        search_query = search_query.options(
            selectinload(Ministry.leader),
            selectinload(Ministry.user_ministries)
        ).order_by(Ministry.name)
        
        result = await self.session.execute(search_query)
        return list(result.scalars().all())