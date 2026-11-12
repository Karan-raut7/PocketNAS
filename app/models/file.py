from sqlalchemy import (
    Integer, String, BigInteger,
    DateTime, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    storage_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    uploaded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    owner = relationship("User", back_populates="files")