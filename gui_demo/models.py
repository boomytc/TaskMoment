from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# --------------------------- Database --------------------------------------

Base = declarative_base()


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<Tag {self.tag}>"


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)

    tag_id = Column(Integer, ForeignKey("tag.id"), nullable=True)
    tag = relationship("Tag", backref="tasks")

    def display_title(self):
        """Return title with #tag appended (for UI display)."""
        if self.tag:
            return f"{self.title} #{self.tag.tag}"
        return self.title


# 在当前文件夹下创建数据库
CURRENT_DIR = Path(__file__).resolve().parent
DB_PATH = CURRENT_DIR / "tasks.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

# Create tables if they do not exist
Base.metadata.create_all(engine)
