import datetime as dt
import enum
import secrets
import uuid

from sqlmodel import Field, SQLModel, UniqueConstraint


class BookingSource(str, enum.Enum):
    airbnb = "airbnb"
    booking = "booking"
    manual = "manual"
    ical = "ical"
    personal = "personal"  # Modo uso personal / bloqueo


class Booking(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("property_id", "external_uid"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    property_id: uuid.UUID = Field(foreign_key="property.id", index=True)
    source: BookingSource = BookingSource.manual
    external_uid: str | None = None
    guest_name: str = ""
    check_in: dt.date
    check_out: dt.date
    total_price: float = 0.0
    status: str = "confirmed"
    # Token público para la guía del huésped (sin login).
    guide_token: str = Field(default_factory=lambda: secrets.token_urlsafe(16), unique=True)
