import uuid

from sqlmodel import JSON, Column, Field, SQLModel


class Property(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str
    city: str = "Málaga"
    address: str = ""
    nightly_price: float = 100.0
    cleaning_fee: float = 0.0
    ical_url: str | None = None
    # Guía digital del huésped.
    wifi_name: str = ""
    wifi_password: str = ""
    checkin_instructions: str = ""
    house_rules: str = ""
    emergency_contacts: dict = Field(default_factory=dict, sa_column=Column(JSON))
