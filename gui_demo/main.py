import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget

from models import Session
from task_tab import TaskTab
from tag_tab import TagTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务清单")
        self.resize(800, 600)

        self.session = Session()

        central = QWidget()
        self.setCentralWidget(central)

        vbox = QVBoxLayout(central)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        vbox.addWidget(self.tab_widget)
        
        # 创建任务管理标签页
        self.task_tab = TaskTab(self.session)
        self.tab_widget.addTab(self.task_tab, "任务管理")
        
        # 创建标签管理标签页
        self.tag_tab = TagTab(self.session)
        self.tab_widget.addTab(self.tag_tab, "标签管理")
        
        # 连接标签页切换信号
        self.tab_widget.currentChanged.connect(self.handle_tab_changed)
        
        # 连接任务变更信号，当任务数据变更时更新标签管理标签页
        self.task_tab.task_changed.connect(self.update_tag_tab)

    def handle_tab_changed(self, index):
        # 根据切换的标签页刷新数据
        if index == 0:  # 任务管理标签页
            self.task_tab.load_tasks()
            self.task_tab._refresh_tag_combo()
        elif index == 1:  # 标签管理标签页
            self.tag_tab.load_tags()  # 刷新标签列表及任务数量
            
    def update_tag_tab(self):
        """当任务数据变更时更新标签管理标签页"""
        # 如果当前标签页是标签管理，则立即刷新
        if self.tab_widget.currentIndex() == 1:
            self.tag_tab.load_tags()


# --------------------------- Entry Point -----------------------------------

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
