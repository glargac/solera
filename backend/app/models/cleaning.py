import datetime as dt
import enum
import uuid

from sqlmodel import JSON, Column, Field, SQLModel


class CleaningStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class CleaningTask(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    property_id: uuid.UUID = Field(foreign_key="property.id", index=True)
    booking_id: uuid.UUID | None = Field(default=None, foreign_key="booking.id", unique=True)
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    date: dt.date = Field(index=True)
    status: CleaningStatus = CleaningStatus.pending
    photo_urls: list = Field(default_factory=list, sa_column=Column(JSON))
