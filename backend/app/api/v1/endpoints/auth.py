from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return user
