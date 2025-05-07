import sys
from PySide6.QtWidgets import QApplication

from app.utils.db import init_database  # Updated import
from app.views.main_window import MainWindow

def main():
    """应用程序入口函数"""
    # 初始化数据库并获取会话工厂
    SessionMaker = init_database()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建主窗口，并传入会话工厂
    window = MainWindow(SessionMaker)
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
