"""
Seed the database with 3 demo users on first startup.
Safe to call multiple times — skips existing users.
"""
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_USERS = [
    {"name": "Alice", "email": "alice@ajaia.com", "password": "password123"},
    {"name": "Bob", "email": "bob@ajaia.com", "password": "password123"},
    {"name": "Carol", "email": "carol@ajaia.com", "password": "password123"},
]


def seed_users(db: Session):
    for u in SEED_USERS:
        exists = db.query(User).filter(User.email == u["email"]).first()
        if not exists:
            user = User(
                name=u["name"],
                email=u["email"],
                hashed_password=pwd_context.hash(u["password"]),
            )
            db.add(user)
    db.commit()
