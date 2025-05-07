from PySide6.QtCore import Qt, QDate, Signal, QThreadPool, Slot
from PySide6.QtGui import QColor, QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QCalendarWidget, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QDialog, QLabel, QMessageBox, QGridLayout, QListWidget, 
    QListWidgetItem, QAbstractItemView, QComboBox, QCheckBox, QMenu, QDateEdit,
    QFrame, QToolButton, QSizePolicy, QButtonGroup, QRadioButton, QGroupBox
)
from datetime import date

from app.controllers.task_controller import TaskController
from app.controllers.tag_controller import TagController
from app.models.task import Task, Priority
from app.workers import GetAllTasksWorker, FilterTasksWorker

class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, tag_controller: TagController, task_controller: TaskController, task=None, parent=None):
        """初始化对话框
        
        Args:
            tag_controller: 标签控制器
            task_controller: 任务控制器
            task: 要编辑的任务，如果为None则为新建任务
            parent: 父窗口
        """
        super().__init__(parent)
        self.tag_controller = tag_controller
        self.task_controller = task_controller
        self.task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        
        self._init_ui()
        
        # 如果是编辑任务，填充表单
        if task:
            self._load_task_data()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("任务标题")
        layout.addWidget(QLabel("标题:"))
        layout.addWidget(self.title_edit)

        self.due_date_edit = QDateEdit(self)
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setSpecialValueText("无截止日期")
        layout.addWidget(QLabel("截止日期:"))
        layout.addWidget(self.due_date_edit)

        self.priority_combo = QComboBox()
        self.priority_combo.addItem("无", Priority.NONE)
        self.priority_combo.addItem("低", Priority.LOW)
        self.priority_combo.addItem("中", Priority.MEDIUM)
        self.priority_combo.addItem("高", Priority.HIGH)
        layout.addWidget(QLabel("优先级:"))
        layout.addWidget(self.priority_combo)

        self.tags_list_widget = QListWidget()
        self.tags_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        all_tags = self.tag_controller.get_all_tags()
        self.tag_map = {}
        for tag_obj in all_tags:
            item = QListWidgetItem(tag_obj.tag)
            item.setData(Qt.UserRole, tag_obj.id)
            self.tags_list_widget.addItem(item)
            self.tag_map[tag_obj.id] = item
        layout.addWidget(QLabel("标签:"))
        layout.addWidget(self.tags_list_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_task_data(self):
        """加载任务数据到UI"""
        self.title_edit.setText(self.task.title)
        if self.task.due_date and self.task.due_date != date(1752, 9, 14):
            self.due_date_edit.setDate(QDate(self.task.due_date.year, self.task.due_date.month, self.task.due_date.day))
        else:
            self.due_date_edit.setDate(self.due_date_edit.minimumDate()) 

        # 确保优先级值有效，如果无效则使用默认值
        priority_value = Priority.NONE
        if hasattr(self.task, 'priority') and self.task.priority is not None:
            if isinstance(self.task.priority, int):
                priority_value = self.task.priority
        
        # 手动设置优先级，而不使用findData
        if priority_value == Priority.NONE:
            self.priority_combo.setCurrentIndex(0)  # 无
        elif priority_value == Priority.LOW:
            self.priority_combo.setCurrentIndex(1)  # 低
        elif priority_value == Priority.MEDIUM:
            self.priority_combo.setCurrentIndex(2)  # 中
        elif priority_value == Priority.HIGH:
            self.priority_combo.setCurrentIndex(3)  # 高
        else:
            # 如果是其他值，默认设置为无
            self.priority_combo.setCurrentIndex(0)
        
        for tag_obj in self.task.tags:
            if tag_obj.id in self.tag_map:
                self.tag_map[tag_obj.id].setSelected(True)

    def get_task_data(self):
        """获取表单数据
        
        Returns:
            包含任务数据的字典，如果标题为空则返回None
        """
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "输入错误", "标题不能为空。")
            return None

        due_date_qdate = self.due_date_edit.date()
        due_date_str = None
        if due_date_qdate != self.due_date_edit.minimumDate():
            due_date_str = due_date_qdate.toString("yyyy-MM-dd")

        # 确保priority始终有一个有效值，默认为Priority.NONE
        priority = self.priority_combo.currentData()
        if priority is None:
            priority = Priority.NONE
        
        selected_tag_ids = []
        for item in self.tags_list_widget.selectedItems():
            selected_tag_ids.append(item.data(Qt.UserRole))

        data = {
            'title': title,
            'due_date': due_date_str,
            'priority': priority,
            'tag_ids': selected_tag_ids
        }
        if self.task: 
            data['completed'] = self.task.completed # 保留现有完成状态
        return data


class TaskTab(QWidget):
    """任务管理标签页"""
    
    # 定义信号
    task_changed = Signal()
    
    def __init__(self, task_controller: TaskController, tag_controller: TagController, SessionMaker, parent=None):
        """初始化任务管理标签页
        
        Args:
            task_controller: 任务控制器
            tag_controller: 标签控制器
            SessionMaker: 数据库会话生成器
            parent: 父窗口
        """
        super().__init__(parent)
        self.task_controller = task_controller
        self.tag_controller = tag_controller
        self.SessionMaker = SessionMaker
        self.thread_pool = QThreadPool()
        
        # 筛选条件状态
        self.current_filters = {
            "keyword": None,
            "due_date_filter": None,
            "status": None,
            "priority": None,
            "tag_ids": None
        }
        
        self._init_ui()
        self.load_tasks()

    def _init_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 搜索区域
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_layout = QHBoxLayout(search_frame)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索任务标题...")
        self.search_input.returnPressed.connect(self.apply_filters)
        
        # 搜索按钮
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.apply_filters)
        
        # 展开/折叠筛选选项按钮
        self.toggle_filter_button = QPushButton("高级筛选 ▼")
        self.toggle_filter_button.setCheckable(True)
        self.toggle_filter_button.setChecked(False)
        self.toggle_filter_button.clicked.connect(self.toggle_filter_options)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(self.toggle_filter_button)
        
        layout.addWidget(search_frame)
        
        # 高级筛选选项（默认折叠）
        self.filter_options_frame = QFrame()
        self.filter_options_frame.setFrameShape(QFrame.StyledPanel)
        filter_options_layout = QVBoxLayout(self.filter_options_frame)
        
        # 筛选选项
        filter_groups_layout = QHBoxLayout()
        
        # 完成状态筛选
        status_group = QGroupBox("完成状态")
        status_layout = QHBoxLayout()
        self.status_group = QButtonGroup(self)
        self.status_all = QRadioButton("全部")
        self.status_completed = QRadioButton("已完成")
        self.status_uncompleted = QRadioButton("未完成")
        self.status_all.setChecked(True)
        self.status_group.addButton(self.status_all, 0)
        self.status_group.addButton(self.status_completed, 1)
        self.status_group.addButton(self.status_uncompleted, 2)
        status_layout.addWidget(self.status_all)
        status_layout.addWidget(self.status_completed)
        status_layout.addWidget(self.status_uncompleted)
        status_group.setLayout(status_layout)
        filter_groups_layout.addWidget(status_group)
        
        # 优先级筛选
        priority_group = QGroupBox("优先级")
        priority_layout = QHBoxLayout()
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("全部", -1)
        self.priority_combo.addItem("无", Priority.NONE)
        self.priority_combo.addItem("低", Priority.LOW)
        self.priority_combo.addItem("中", Priority.MEDIUM)
        self.priority_combo.addItem("高", Priority.HIGH)
        priority_layout.addWidget(self.priority_combo)
        priority_group.setLayout(priority_layout)
        filter_groups_layout.addWidget(priority_group)
        
        # 截止日期筛选
        due_date_group = QGroupBox("截止日期")
        due_date_layout = QHBoxLayout()
        self.due_date_combo = QComboBox()
        self.due_date_combo.addItem("全部", "")
        self.due_date_combo.addItem("今天", "today")
        self.due_date_combo.addItem("明天", "tomorrow")
        self.due_date_combo.addItem("本周内", "week")
        self.due_date_combo.addItem("已逾期", "overdue")
        self.due_date_combo.addItem("未来", "future")
        self.due_date_combo.addItem("无截止日期", "none")
        due_date_layout.addWidget(self.due_date_combo)
        due_date_group.setLayout(due_date_layout)
        filter_groups_layout.addWidget(due_date_group)
        
        filter_options_layout.addLayout(filter_groups_layout)
        
        # 标签筛选
        tags_group = QGroupBox("标签筛选")
        tags_layout = QHBoxLayout()
        self.tags_combo = QComboBox()
        self.tags_combo.addItem("全部标签", -1)
        all_tags = self.tag_controller.get_all_tags()
        for tag in all_tags:
            self.tags_combo.addItem(f"#{tag.tag}", tag.id)
        tags_layout.addWidget(self.tags_combo)
        tags_group.setLayout(tags_layout)
        filter_options_layout.addWidget(tags_group)
        
        # 筛选按钮区域
        filter_buttons_layout = QHBoxLayout()
        apply_filter_button = QPushButton("应用筛选")
        apply_filter_button.clicked.connect(self.apply_filters)
        reset_filter_button = QPushButton("重置筛选")
        reset_filter_button.clicked.connect(self.reset_filters)
        filter_buttons_layout.addWidget(apply_filter_button)
        filter_buttons_layout.addWidget(reset_filter_button)
        filter_options_layout.addLayout(filter_buttons_layout)
        
        # 默认隐藏高级筛选选项
        self.filter_options_frame.setVisible(False)
        layout.addWidget(self.filter_options_frame)
        
        # 筛选结果统计
        self.filter_stats_label = QLabel("显示全部任务")
        layout.addWidget(self.filter_stats_label)
        
        # 添加任务按钮
        add_button = QPushButton("添加任务")
        add_button.clicked.connect(self.open_add_task_dialog)
        layout.addWidget(add_button)
        
        # 任务表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "标题", "截止日期", "优先级", "标签", "完成"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self.open_edit_task_dialog_on_double_click)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def load_tasks(self):
        """异步加载任务列表"""
        # 清空表格
        self.table.setRowCount(0)
        
        # 根据当前筛选条件加载任务
        self.apply_current_filters()

    @Slot(object)
    def _on_load_tasks_finished(self, result):
        """任务加载完成后的处理"""
        # 解包结果
        tasks, stats = result
        
        # 清空表格
        self.table.setRowCount(0)
        
        # 添加任务到表格
        for task in tasks:
            self._add_task_to_table(task)
            
        # 更新统计信息
        self.update_filter_stats(stats)

    @Slot(str)
    def _on_load_tasks_error(self, error_message):
        """任务加载错误处理"""
        QMessageBox.critical(self, "加载任务失败", error_message)

    def _add_task_to_table(self, task):
        """将任务添加到表格"""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # ID (隐藏)
        id_item = QTableWidgetItem(str(task.id))
        self.table.setItem(row_position, 0, id_item)
        self.table.setColumnHidden(0, True)

        # 标题
        title_item = QTableWidgetItem(task.title)
        if task.completed:
            font = title_item.font()
            font.setStrikeOut(True)
            title_item.setFont(font)
            title_item.setForeground(QColor("gray"))
        title_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 1, title_item)

        # 截止日期
        due_date_str = "无截止日期"
        if task.due_date:
            if task.due_date == date(1752, 9, 14):
                due_date_str = "无截止日期"
            else:
                due_date_str = task.due_date.strftime("%Y-%m-%d")
        due_date_item = QTableWidgetItem(due_date_str)
        due_date_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 2, due_date_item)

        # 优先级
        priority_item = QTableWidgetItem(task.get_priority_name())
        priority_item.setForeground(QColor(task.get_priority_color()))
        priority_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 3, priority_item)

        # 标签
        tags_str = ", ".join([tag.tag for tag in task.tags])
        tags_item = QTableWidgetItem(tags_str)
        tags_item.setTextAlignment(Qt.AlignCenter) # 居中对齐
        self.table.setItem(row_position, 4, tags_item)

        # 完成状态 (复选框)
        completed_checkbox = QCheckBox()
        completed_checkbox.setChecked(task.completed)
        completed_checkbox.clicked.connect(lambda checked, task_id=task.id: self.toggle_task_completed_status(task_id, checked))
        
        # 创建一个容器 QWidget 用于居中复选框
        cell_widget = QWidget()
        layout_checkbox = QHBoxLayout(cell_widget)
        layout_checkbox.addWidget(completed_checkbox)
        layout_checkbox.setAlignment(Qt.AlignCenter) # 布局居中
        layout_checkbox.setContentsMargins(0,0,0,0) # 移除边距
        cell_widget.setLayout(layout_checkbox) # 设置布局到容器

        self.table.setCellWidget(row_position, 5, cell_widget) # 将容器 QWidget 设置为单元格小部件

    def open_add_task_dialog(self):
        """打开添加任务对话框"""
        dialog = TaskEditDialog(self.tag_controller, self.task_controller, parent=self)
        if dialog.exec():
            data = dialog.get_task_data()
            if data:
                self.task_controller.create_task(**data)
                self.apply_current_filters()
                self.task_changed.emit()

    def open_edit_task_dialog_on_double_click(self, item):
        """双击打开编辑任务对话框"""
        row = item.row()
        self.open_edit_task_dialog(row)

    def open_edit_task_dialog(self, row):
        """打开编辑任务对话框"""
        task_id = int(self.table.item(row, 0).text())
        task = self.task_controller.get_task_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "找不到任务")
            return

        dialog = TaskEditDialog(self.tag_controller, self.task_controller, task=task, parent=self)
        if dialog.exec():
            data = dialog.get_task_data()
            if data:
                self.task_controller.update_task(task_id, data)
                self.apply_current_filters()
                self.task_changed.emit()

    def delete_task(self, row):
        """删除任务"""
        task_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "确认删除", "确定要删除此任务吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.task_controller.delete_task(task_id)
            self.apply_current_filters()
            self.task_changed.emit()

    def toggle_task_completed_status(self, task_id, checked):
        """切换任务完成状态"""
        self.task_controller.toggle_task_completed(task_id)
        self.apply_current_filters()
        self.task_changed.emit()

    def show_context_menu(self, pos):
        """显示右键菜单"""
        context_menu = QMenu(self)
        edit_action = QAction("编辑任务", self)
        delete_action = QAction("删除任务", self)
        
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        
        edit_action.triggered.connect(lambda: self.open_edit_task_dialog(row))
        delete_action.triggered.connect(lambda: self.delete_task(row))
        
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        context_menu.exec(self.table.mapToGlobal(pos))
        
    def apply_filters(self):
        """应用筛选条件"""
        # 获取关键词
        keyword = self.search_input.text().strip() if self.search_input.text().strip() else None
        
        # 获取完成状态
        status = None
        if self.status_completed.isChecked():
            status = True
        elif self.status_uncompleted.isChecked():
            status = False
        
        # 获取优先级
        priority = None
        if self.priority_combo.currentData() != -1:
            priority = self.priority_combo.currentData()
        
        # 获取截止日期筛选
        due_date_filter = None
        if self.due_date_combo.currentData():
            due_date_filter = self.due_date_combo.currentData()
        
        # 获取标签筛选
        tag_ids = None
        if self.tags_combo.currentData() != -1:
            tag_ids = [self.tags_combo.currentData()]
        
        # 更新当前筛选条件
        self.current_filters = {
            "keyword": keyword,
            "due_date_filter": due_date_filter,
            "status": status,
            "priority": priority,
            "tag_ids": tag_ids
        }
        
        # 应用筛选
        self.apply_current_filters()
    
    def reset_filters(self):
        """重置所有筛选条件"""
        # 重置搜索框
        self.search_input.clear()
        
        # 重置完成状态
        self.status_all.setChecked(True)
        
        # 重置优先级
        self.priority_combo.setCurrentIndex(0)
        
        # 重置截止日期
        self.due_date_combo.setCurrentIndex(0)
        
        # 重置标签
        self.tags_combo.setCurrentIndex(0)
        
        # 清空当前筛选条件
        self.current_filters = {
            "keyword": None,
            "due_date_filter": None,
            "status": None,
            "priority": None,
            "tag_ids": None
        }
        
        # 重新加载所有任务
        self.apply_current_filters()
    
    def apply_current_filters(self):
        """应用当前的筛选条件"""
        # 创建工作线程加载任务
        worker = FilterTasksWorker(
            self.task_controller,
            self.current_filters["keyword"],
            self.current_filters["due_date_filter"],
            self.current_filters["status"],
            self.current_filters["priority"],
            self.current_filters["tag_ids"]
        )
        worker.signals.result.connect(self._on_load_tasks_finished)
        worker.signals.error.connect(self._on_load_tasks_error)
        QThreadPool.globalInstance().start(worker)
    
    def update_filter_stats(self, stats):
        """更新筛选统计信息"""
        if stats["has_filter"]:
            self.filter_stats_label.setText(
                f"筛选结果: 共{stats['total_count']}个任务 (已完成: {stats['completed_count']}, 未完成: {stats['total_count'] - stats['completed_count']})"
            )
        else:
            self.filter_stats_label.setText(
                f"显示全部任务: 共{stats['total_count']}个任务 (已完成: {stats['completed_count']}, 未完成: {stats['total_count'] - stats['completed_count']})"
            )
    
    def toggle_filter_options(self):
        """切换筛选选项的显示/隐藏"""
        is_visible = not self.filter_options_frame.isVisible()
        self.filter_options_frame.setVisible(is_visible)
        
        # 更新按钮文本
        if is_visible:
            self.toggle_filter_button.setText("高级筛选 ▲")
        else:
            self.toggle_filter_button.setText("高级筛选 ▼")
