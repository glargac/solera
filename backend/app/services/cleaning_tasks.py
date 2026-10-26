from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models import Booking, BookingSource, CleaningTask


async def ensure_cleaning_task(session: AsyncSession, booking: Booking) -> None:
    """Crea la tarea de limpieza del día de checkout si no existe."""
    if booking.source == BookingSource.personal:
        return
    existing = await session.exec(
        select(CleaningTask).where(CleaningTask.booking_id == booking.id)
    )
    task = existing.first()
    if task is None:
        session.add(
            CleaningTask(
                property_id=booking.property_id,
                booking_id=booking.id,
                date=booking.check_out,
            )
        )
    elif task.date != booking.check_out:
        task.date = booking.check_out
        session.add(task)
