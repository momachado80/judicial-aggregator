from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Schema para registro de novo usuário
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

# Schema para login
class UserLogin(BaseModel):
    username: str
    password: str

# Schema de resposta (não retorna senha)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Schema para token JWT
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
