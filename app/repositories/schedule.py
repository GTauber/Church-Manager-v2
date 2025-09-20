"""
Schedule repository for database operations.

Provides specialized methods for Schedule, ScheduleOccurrence,
and ScheduleAssignment model operations.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.schedule import (
    Schedule,
    ScheduleOccurrence,
    ScheduleAssignment,
    RoleCode,
    StatusCode,
)
from app.models.user import User
from app.models.ministry import Ministry
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    """
    Repository for Schedule model operations.
    
    Extends BaseRepository with Schedule-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ScheduleRepository with Schedule model."""
        super().__init__(Schedule, session)
    
    async def get_ministry_schedules(
        self,
        ministry_id: UUID,
        active_only: bool = True
    ) -> List[Schedule]:
        """
        Get all schedules for a ministry.
        
        Args:
            ministry_id: The ministry ID
            active_only: Whether to filter only current/future schedules
            
        Returns:
            List of schedules
        """
        query = select(Schedule).where(Schedule.ministry_id == ministry_id)
        
        if active_only:
            today = date.today()
            query = query.where(Schedule.end_date >= today)
        
        query = query.options(
            selectinload(Schedule.ministry),
            selectinload(Schedule.occurrences).selectinload(ScheduleOccurrence.assignments)
        ).order_by(Schedule.start_date.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_schedules_in_range(
        self,
        start_date: date,
        end_date: date,
        ministry_id: UUID = None
    ) -> List[Schedule]:
        """
        Get schedules within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            ministry_id: Optional ministry filter
            
        Returns:
            List of schedules in the range
        """
        query = select(Schedule).where(
            and_(
                Schedule.start_date <= end_date,
                Schedule.end_date >= start_date
            )
        )
        
        if ministry_id:
            query = query.where(Schedule.ministry_id == ministry_id)
        
        query = query.options(
            selectinload(Schedule.ministry),
            selectinload(Schedule.occurrences)
        ).order_by(Schedule.start_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_schedule_with_occurrences(
        self,
        ministry_id: UUID,
        title: str,
        start_date: date,
        end_date: date,
        occurrence_dates: List[date],
        notes: str = None
    ) -> Schedule:
        """
        Create a schedule with multiple occurrences.
        
        Args:
            ministry_id: The ministry ID
            title: Schedule title
            start_date: Start date
            end_date: End date
            occurrence_dates: List of dates for occurrences
            notes: Optional notes
            
        Returns:
            Created schedule with occurrences
        """
        # Create the schedule
        schedule = await self.create(
            ministry_id=ministry_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            notes=notes
        )
        
        # Create occurrences
        for occ_date in occurrence_dates:
            if start_date <= occ_date <= end_date:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                       "Friday", "Saturday", "Sunday"]
                day_of_week = days[occ_date.weekday()]
                
                occurrence = ScheduleOccurrence(
                    schedule_id=schedule.id,
                    occurrence_date=occ_date,
                    day_of_week=day_of_week
                )
                self.session.add(occurrence)
        
        await self.session.flush()
        await self.session.refresh(schedule)
        
        return schedule


class ScheduleOccurrenceRepository(BaseRepository[ScheduleOccurrence]):
    """
    Repository for ScheduleOccurrence model operations.
    
    Extends BaseRepository with ScheduleOccurrence-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ScheduleOccurrenceRepository with ScheduleOccurrence model."""
        super().__init__(ScheduleOccurrence, session)
    
    async def get_occurrences_by_date(
        self,
        occurrence_date: date,
        ministry_id: UUID = None
    ) -> List[ScheduleOccurrence]:
        """
        Get all occurrences on a specific date.
        
        Args:
            occurrence_date: The date to query
            ministry_id: Optional ministry filter
            
        Returns:
            List of occurrences on that date
        """
        query = select(ScheduleOccurrence).where(
            ScheduleOccurrence.occurrence_date == occurrence_date
        )
        
        if ministry_id:
            query = query.join(Schedule).where(Schedule.ministry_id == ministry_id)
        
        query = query.options(
            selectinload(ScheduleOccurrence.schedule).selectinload(Schedule.ministry),
            selectinload(ScheduleOccurrence.assignments).selectinload(ScheduleAssignment.user)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_occurrences_in_range(
        self,
        start_date: date,
        end_date: date,
        ministry_id: UUID = None
    ) -> List[ScheduleOccurrence]:
        """
        Get occurrences within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            ministry_id: Optional ministry filter
            
        Returns:
            List of occurrences in the range
        """
        query = select(ScheduleOccurrence).where(
            and_(
                ScheduleOccurrence.occurrence_date >= start_date,
                ScheduleOccurrence.occurrence_date <= end_date
            )
        )
        
        if ministry_id:
            query = query.join(Schedule).where(Schedule.ministry_id == ministry_id)
        
        query = query.options(
            selectinload(ScheduleOccurrence.schedule).selectinload(Schedule.ministry),
            selectinload(ScheduleOccurrence.assignments).selectinload(ScheduleAssignment.user)
        ).order_by(ScheduleOccurrence.occurrence_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_upcoming_occurrences(
        self,
        days_ahead: int = 30,
        ministry_id: UUID = None
    ) -> List[ScheduleOccurrence]:
        """
        Get upcoming occurrences.
        
        Args:
            days_ahead: Number of days to look ahead
            ministry_id: Optional ministry filter
            
        Returns:
            List of upcoming occurrences
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        return await self.get_occurrences_in_range(today, end_date, ministry_id)


class ScheduleAssignmentRepository(BaseRepository[ScheduleAssignment]):
    """
    Repository for ScheduleAssignment model operations.
    
    Extends BaseRepository with ScheduleAssignment-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ScheduleAssignmentRepository with ScheduleAssignment model."""
        super().__init__(ScheduleAssignment, session)
    
    async def create_assignment(
        self,
        occurrence_id: UUID,
        user_id: UUID,
        role_code: str,
        status_code: str = StatusCode.ASSIGNED.value,
        notes: str = None
    ) -> ScheduleAssignment:
        """
        Create a schedule assignment.
        
        Args:
            occurrence_id: The occurrence ID
            user_id: The user ID
            role_code: The role code
            status_code: Initial status (defaults to ASSIGNED)
            notes: Optional notes
            
        Returns:
            Created assignment
        """
        # Validate role and status codes
        if role_code not in [r.value for r in RoleCode]:
            raise ValueError(f"Invalid role code: {role_code}")
        
        if status_code not in [s.value for s in StatusCode]:
            raise ValueError(f"Invalid status code: {status_code}")
        
        return await self.create(
            occurrence_id=occurrence_id,
            user_id=user_id,
            role_code=role_code,
            status_code=status_code,
            notes=notes
        )
    
    async def get_user_assignments(
        self,
        user_id: UUID,
        start_date: date = None,
        end_date: date = None,
        status_codes: List[str] = None
    ) -> List[ScheduleAssignment]:
        """
        Get assignments for a user.
        
        Args:
            user_id: The user ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            status_codes: Optional list of status codes to filter
            
        Returns:
            List of assignments
        """
        query = select(ScheduleAssignment).where(
            ScheduleAssignment.user_id == user_id
        )
        
        if status_codes:
            query = query.where(ScheduleAssignment.status_code.in_(status_codes))
        
        # Join with occurrence for date filtering
        query = query.join(ScheduleOccurrence)
        
        if start_date:
            query = query.where(ScheduleOccurrence.occurrence_date >= start_date)
        
        if end_date:
            query = query.where(ScheduleOccurrence.occurrence_date <= end_date)
        
        query = query.options(
            selectinload(ScheduleAssignment.occurrence)
            .selectinload(ScheduleOccurrence.schedule)
            .selectinload(Schedule.ministry)
        ).order_by(ScheduleOccurrence.occurrence_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_occurrence_assignments(
        self,
        occurrence_id: UUID,
        role_code: str = None
    ) -> List[ScheduleAssignment]:
        """
        Get all assignments for an occurrence.
        
        Args:
            occurrence_id: The occurrence ID
            role_code: Optional role filter
            
        Returns:
            List of assignments
        """
        query = select(ScheduleAssignment).where(
            ScheduleAssignment.occurrence_id == occurrence_id
        )
        
        if role_code:
            query = query.where(ScheduleAssignment.role_code == role_code)
        
        query = query.options(
            selectinload(ScheduleAssignment.user)
        ).order_by(ScheduleAssignment.role_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_assignment_status(
        self,
        assignment_id: UUID,
        new_status: StatusCode,
        notes: str = None
    ) -> Optional[ScheduleAssignment]:
        """
        Update the status of an assignment.
        
        Args:
            assignment_id: The assignment ID
            new_status: New status code
            notes: Optional notes about the status change
            
        Returns:
            Updated assignment or None if not found
        """
        assignment = await self.get(assignment_id)
        if not assignment:
            return None
        
        # Check if transition is allowed
        if not assignment.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {assignment.status_code} to {new_status.value}"
            )
        
        update_data = {"status_code": new_status.value}
        if notes:
            update_data["notes"] = notes
        
        return await self.update(assignment_id, **update_data)
    
    async def bulk_assign_occurrence(
        self,
        occurrence_id: UUID,
        assignments: List[Dict[str, Any]]
    ) -> List[ScheduleAssignment]:
        """
        Create multiple assignments for an occurrence.
        
        Args:
            occurrence_id: The occurrence ID
            assignments: List of assignment data (user_id, role_code, notes)
            
        Returns:
            List of created assignments
        """
        created_assignments = []
        
        for assignment_data in assignments:
            assignment = await self.create_assignment(
                occurrence_id=occurrence_id,
                user_id=assignment_data["user_id"],
                role_code=assignment_data["role_code"],
                notes=assignment_data.get("notes")
            )
            created_assignments.append(assignment)
        
        return created_assignments
    
    async def get_assignment_statistics(
        self,
        start_date: date,
        end_date: date,
        ministry_id: UUID = None
    ) -> Dict[str, Any]:
        """
        Get assignment statistics for a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            ministry_id: Optional ministry filter
            
        Returns:
            Dictionary with statistics
        """
        query = (
            select(
                ScheduleAssignment.status_code,
                func.count(ScheduleAssignment.id).label("count")
            )
            .join(ScheduleOccurrence)
            .where(
                and_(
                    ScheduleOccurrence.occurrence_date >= start_date,
                    ScheduleOccurrence.occurrence_date <= end_date
                )
            )
        )
        
        if ministry_id:
            query = query.join(Schedule).where(Schedule.ministry_id == ministry_id)
        
        query = query.group_by(ScheduleAssignment.status_code)
        
        result = await self.session.execute(query)
        stats = {row.status_code: row.count for row in result}
        
        # Calculate totals
        total = sum(stats.values())
        confirmed_rate = (stats.get(StatusCode.CONFIRMED.value, 0) / total * 100) if total > 0 else 0
        
        return {
            "total_assignments": total,
            "by_status": stats,
            "confirmation_rate": round(confirmed_rate, 2)
        }