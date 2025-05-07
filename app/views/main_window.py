from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget

from app.views.task_tab import TaskTab
from app.views.tag_tab import TagTab
from app.controllers.task_controller import TaskController
from app.controllers.tag_controller import TagController

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, SessionMaker):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("TaskMoment")
        self.resize(800, 600)
        
        self.SessionMaker = SessionMaker
        self.session = self.SessionMaker()
        
        # 创建控制器实例
        self.task_controller = TaskController(self.session)
        self.tag_controller = TagController(self.session)

        # 中心控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        vbox = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        vbox.addWidget(self.tab_widget)
        
        # 创建任务管理标签页
        self.task_tab = TaskTab(self.task_controller, self.tag_controller, self.SessionMaker)
        self.tab_widget.addTab(self.task_tab, "任务管理")
        
        # 创建标签管理标签页
        self.tag_tab = TagTab(self.tag_controller) 
        self.tab_widget.addTab(self.tag_tab, "标签管理")
        
        # 连接标签页切换信号
        self.tab_widget.currentChanged.connect(self.handle_tab_changed)
        
        # 连接任务变更信号
        self.task_tab.task_changed.connect(self.handle_task_changed)
    
    def handle_tab_changed(self, index):
        """处理标签页切换
        
        Args:
            index: 标签页索引
        """
        # 根据切换的标签页刷新数据
        if index == 0:  # 任务管理标签页
            self.task_tab.load_tasks()
        elif index == 1:  # 标签管理标签页
            self.tag_tab.load_tags()
    
    def handle_task_changed(self):
        """处理任务变更事件"""
        # 如果当前是标签管理标签页，刷新标签列表
        if self.tab_widget.currentIndex() == 1:
            self.tag_tab.load_tags()
    
    def closeEvent(self, event):
        """处理窗口关闭事件
        
        Args:
            event: 关闭事件
        """
        # 关闭数据库会话
        if self.session:
            self.session.close()
        
        # 等待线程池完成
        QThreadPool.globalInstance().waitForDone()
        event.accept()
