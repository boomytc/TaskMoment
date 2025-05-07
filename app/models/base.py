from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

# 创建基础模型类
Base = declarative_base()

# 任务标签关联表（多对多关系）
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('task.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

# Removed global engine, Session, and init_db() function from here.
# Database initialization is now handled by app.utils.db.init_database
