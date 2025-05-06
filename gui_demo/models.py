from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# --------------------------- Database --------------------------------------

Base = declarative_base()

# 任务标签关联表（多对多关系）
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('task.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)


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

    # 移除单一标签关系
    # tag_id = Column(Integer, ForeignKey("tag.id"), nullable=True)
    # tag = relationship("Tag", backref="tasks")
    
    # 添加多对多标签关系
    tags = relationship("Tag", secondary=task_tags, backref="tasks")

    def display_title(self):
        """返回带有标签的任务标题（用于UI显示）"""
        if not self.tags:
            return self.title
            
        # 将所有标签添加到标题后面
        tags_str = " ".join([f"#{tag.tag}" for tag in self.tags])
        return f"{self.title} {tags_str}"


# 在当前文件夹下创建数据库
CURRENT_DIR = Path(__file__).resolve().parent
DB_PATH = CURRENT_DIR / "tasks.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

# Create tables if they do not exist
Base.metadata.create_all(engine)
