import datetime as dt
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import CleaningStatus, CleaningTask, Property, Role, User
from app.services.storage import upload_photo

router = APIRouter(prefix="/cleaning", tags=["cleaning"])
REQUIRED_PHOTOS = 3


async def _visible(session: AsyncSession, task_id: uuid.UUID, user: User) -> CleaningTask:
    task = await session.get(CleaningTask, task_id)
    if task is None:
        raise HTTPException(404, "Tarea no encontrada")
    if user.role == Role.cleaning_staff:
        ok = task.assigned_to == user.id
    else:
        prop = await session.get(Property, task.property_id)
        ok = prop is not None and prop.owner_id == user.id
    if not ok:
        raise HTTPException(404, "Tarea no encontrada")
    return task


@router.get("/tasks", response_model=list[CleaningTask])
async def list_tasks(
    date: dt.date | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    date = date or dt.date.today()
    q = select(CleaningTask).where(CleaningTask.date == date)
    if user.role == Role.cleaning_staff:
        q = q.where(CleaningTask.assigned_to == user.id)
    elif user.role == Role.host:
        q = q.join(Property, Property.id == CleaningTask.property_id).where(Property.owner_id == user.id)
    else:
        raise HTTPException(403, "Permiso denegado")
    return (await session.exec(q)).all()


@router.put("/tasks/{task_id}/assign/{staff_id}", response_model=CleaningTask)
async def assign(task_id: uuid.UUID, staff_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if user.role != Role.host:
        raise HTTPException(403, "Solo el anfitrión asigna tareas")
    task = await _visible(session, task_id, user)
    staff = await session.get(User, staff_id)
    if staff is None or staff.role != Role.cleaning_staff or staff.host_id != user.id:
        raise HTTPException(404, "Limpiador no encontrado")
    task.assigned_to = staff_id
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.post("/tasks/{task_id}/photos", response_model=CleaningTask)
async def upload_photos(
    task_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    task = await _visible(session, task_id, user)
    paths = list(task.photo_urls)
    for f in files:
        if f.content_type not in ("image/jpeg", "image/png"):
            raise HTTPException(415, "Solo JPEG o PNG")
        paths.append(await upload_photo(await f.read(), f.content_type, f"tasks/{task.id}"))
    task.photo_urls = paths
    task.status = CleaningStatus.in_progress
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.post("/tasks/{task_id}/complete", response_model=CleaningTask)
async def complete(task_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    task = await _visible(session, task_id, user)
    if len(task.photo_urls) < REQUIRED_PHOTOS:
        raise HTTPException(422, f"Se necesitan {REQUIRED_PHOTOS} fotos de control")
    task.status = CleaningStatus.done
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task
