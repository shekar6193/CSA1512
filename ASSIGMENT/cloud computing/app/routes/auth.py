from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication & Roles"])

@router.get("/users")
def get_demo_users(db: Session = Depends(get_db)):
    """
    List predefined demo users across Student, Faculty, Technician, Security, and Admin roles.
    """
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "department": u.department
        }
        for u in users
    ]
