from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# 创建基础模型类
Base = declarative_base()

# 在当前文件夹下创建数据库
CURRENT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = CURRENT_DIR / "data" / "tasks.db"

# 确保数据目录存在
DB_PATH.parent.mkdir(exist_ok=True)

# 创建数据库引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

# 任务标签关联表（多对多关系）
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('task.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

def init_db():
    """初始化数据库"""
    # 创建数据目录
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # 创建表
    Base.metadata.create_all(engine)
    
    return Session()
