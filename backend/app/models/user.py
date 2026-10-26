import enum
import uuid

from sqlmodel import Field, SQLModel


class Role(str, enum.Enum):
    host = "host"
    cleaning_staff = "cleaning_staff"
    guest = "guest"


class User(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)  # = auth.users.id de Supabase
    email: str
    full_name: str = ""
    role: Role = Role.host
    # Para limpiadores: anfitrión que los gestiona.
    host_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
