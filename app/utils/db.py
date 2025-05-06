from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

def init_database(db_path=None):
    """初始化数据库
    
    Args:
        db_path: 数据库路径，如果为None则使用默认路径
        
    Returns:
        数据库会话工厂
    """
    if db_path is None:
        # 默认在项目根目录的data文件夹下创建数据库
        current_dir = Path(__file__).resolve().parent.parent.parent
        db_path = current_dir / "data" / "tasks.db"
    
    # 确保数据目录存在
    db_path.parent.mkdir(exist_ok=True)
    
    # 创建数据库引擎
    engine = create_engine(
        f"sqlite:///{db_path}", 
        echo=False, 
        connect_args={"check_same_thread": False}
    )
    
    # 创建表
    Base.metadata.create_all(engine)
    
    # 创建会话工厂
    Session = sessionmaker(bind=engine)
    
    return Session
