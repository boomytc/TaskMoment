import sys
from PySide6.QtWidgets import QApplication

from app.models.base import Base, init_db
from app.views.main_window import MainWindow

def main():
    """应用程序入口函数"""
    # 初始化数据库
    init_db()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
