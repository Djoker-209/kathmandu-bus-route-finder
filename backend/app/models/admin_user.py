"""
SQLAlchemy ORM model for administrator accounts.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AdminUser(Base):
    """
    Represents an administrator who can access
    protected backend endpoints.
    """

    __tablename__ = "admin_users"

    # ----------------------------------------
    # Primary Key
    # ----------------------------------------
    admin_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # ----------------------------------------
    # Login Credentials
    # ----------------------------------------
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ----------------------------------------
    # Authorization
    # ----------------------------------------
    role: Mapped[str] = mapped_column(
        String(20),
        default="admin",
        nullable=False,
    )

    # ----------------------------------------
    # Metadata
    # ----------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ----------------------------------------
    # Debug Representation
    # ----------------------------------------
    def __repr__(self) -> str:
        return (
            f"AdminUser("
            f"id={self.admin_id}, "
            f"username='{self.username}', "
            f"role='{self.role}')"
        )