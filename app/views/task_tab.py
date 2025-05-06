from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QCalendarWidget, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QDialog, QLabel, QMessageBox, QGridLayout, QListWidget, 
    QListWidgetItem, QAbstractItemView, QComboBox
)

from app.controllers.task_controller import TaskController
from app.controllers.tag_controller import TagController
from app.models.task import Task, Priority
from app.models.tag import Tag

class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, task_controller, tag_controller, task=None, parent=None):
        """初始化对话框
        
        Args:
            task_controller: 任务控制器
            tag_controller: 标签控制器
            task: 要编辑的任务，如果为None则为新建任务
            parent: 父窗口
        """
        super().__init__(parent)
        self.task_controller = task_controller
        self.tag_controller = tag_controller
        self.task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        
        self._init_ui()
        
        # 如果是编辑任务，填充表单
        if task:
            self.set_task_data(task)
    
    def _init_ui(self):
        """初始化UI"""
        # 创建控件
        self.title_edit = QLineEdit()
        
        # 新的日期选择UI
        self.date_display = QLineEdit()
        self.date_display.setPlaceholderText("无截止日期")
        self.date_display.setReadOnly(True)
        self.date_button = QPushButton("📅") # 修正图标
        self.date_button.setToolTip("选择截止日期")
        self.date_button.clicked.connect(self._open_calendar_dialog)

        date_layout = QHBoxLayout()
        date_layout.addWidget(self.date_display)
        date_layout.addWidget(self.date_button)

        # 优先级选择下拉框
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("无优先级", Priority.NONE)
        self.priority_combo.addItem("低优先级", Priority.LOW)
        self.priority_combo.addItem("中优先级", Priority.MEDIUM)
        self.priority_combo.addItem("高优先级", Priority.HIGH)
        
        # 为优先级选项设置颜色
        self.priority_combo.setItemData(0, "#808080", Qt.ForegroundRole)  # 灰色
        self.priority_combo.setItemData(1, "#4D94FF", Qt.ForegroundRole)  # 蓝色
        self.priority_combo.setItemData(2, "#FFD700", Qt.ForegroundRole)  # 黄色
        self.priority_combo.setItemData(3, "#FF4D4D", Qt.ForegroundRole)  # 红色
        
        # 标签列表和添加标签控件
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.tag_list.setMaximumHeight(100)
        
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("输入新标签")
        self.add_tag_btn = QPushButton("+")
        self.add_tag_btn.setMaximumWidth(30)
        
        # 初始化标签列表
        self._init_tag_list()
        
        # 布局
        layout = QGridLayout()
        layout.addWidget(QLabel("任务内容:"), 0, 0)
        layout.addWidget(self.title_edit, 0, 1)
        layout.addWidget(QLabel("截止日期:"), 1, 0)
        layout.addLayout(date_layout, 1, 1) # 使用新的 date_layout
        layout.addWidget(QLabel("优先级:"), 2, 0)
        layout.addWidget(self.priority_combo, 2, 1)
        layout.addWidget(QLabel("标签:"), 3, 0)
        
        # 标签选择区域
        tag_area = QVBoxLayout()
        tag_area.addWidget(self.tag_list)
        
        # 新标签输入区域
        new_tag_layout = QHBoxLayout()
        new_tag_layout.addWidget(self.new_tag_edit)
        new_tag_layout.addWidget(self.add_tag_btn)
        tag_area.addLayout(new_tag_layout)
        
        layout.addLayout(tag_area, 3, 1)
        
        # 按钮区域
        btn_box = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box, 4, 0, 1, 2)
        
        self.setLayout(layout)
        
        # 连接信号
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        self.add_tag_btn.clicked.connect(self._add_new_tag)
    
    def _init_tag_list(self):
        """初始化标签列表"""
        self.tag_list.clear()
        self.tag_map = {}  # 用于存储标签项和标签对象的映射
        
        # 加载所有标签
        for tag in self.tag_controller.get_all_tags():
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
    
    def _open_calendar_dialog(self):
        # 标记是否已选择"无截止日期"
        no_due_date_selected = [False]
        dialog = QDialog(self)
        dialog.setWindowTitle("选择截止日期")
        layout = QVBoxLayout(dialog)

        calendar = QCalendarWidget(dialog)
        calendar.setMinimumDate(QDate.currentDate()) # 只能选择当天及以后
        if self.date_display.text() != "无截止日期" and self.date_display.text():
            try:
                current_date = QDate.fromString(self.date_display.text(), "yyyy-MM-dd")
                if current_date.isValid():
                    calendar.setSelectedDate(current_date)
            except Exception:
                pass # 如果解析失败，则不设置日期

        layout.addWidget(calendar)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset, dialog)
        clear_button = button_box.button(QDialogButtonBox.Reset)
        if clear_button: # QDialogButtonBox.Reset 可能不存在于所有样式中
            clear_button.setText("无截止日期")
            clear_button.clicked.connect(lambda: self._set_no_due_date_edit(dialog, no_due_date_selected))
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # QCalendarWidget 没有直接的清除按钮，我们通过 Reset 按钮实现
        # 如果 Reset 按钮不存在，则需要手动添加一个“清除”按钮
        if not clear_button:
            manual_clear_button = QPushButton("无截止日期")
            manual_clear_button.clicked.connect(lambda: self._set_no_due_date_edit(dialog, no_due_date_selected))
            button_box.addButton(manual_clear_button, QDialogButtonBox.ActionRole)

        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec():
            if no_due_date_selected[0]:
                # 已在_set_no_due_date_edit中设置为"无截止日期"
                pass
            else:
                selected_date = calendar.selectedDate()
                self.date_display.setText(selected_date.toString("yyyy-MM-dd"))
        # 如果用户按下了 Cancel，则不做任何操作

    def _set_no_due_date_edit(self, dialog, no_due_date_flag):
        """设置为无截止日期并关闭对话框"""
        self.date_display.setText("无截止日期")
        no_due_date_flag[0] = True
        dialog.accept()

    def set_task_data(self, task):
        """设置任务数据显示到UI"""
        self.title_edit.setText(task.title)
        if task.due_date:
            # 兼容字符串或 datetime.date 两种类型
            if isinstance(task.due_date, str):
                date_str = task.due_date
            else:
                # 假设为 datetime.date 类型
                date_str = task.due_date.strftime("%Y-%m-%d")
            self.date_display.setText(date_str)
        else:
            self.date_display.setText("无截止日期")
        
        # 设置优先级
        # 将整数的 task.priority 转换为 Priority 枚举成员
        priority_enum_member = Priority(task.priority)
        index = self.priority_combo.findData(priority_enum_member)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)
        
        # 选中任务已有的标签
        for tag in task.tags:
            if tag.id in self.tag_map:
                self.tag_map[tag.id].setSelected(True)
    
    def _add_new_tag(self):
        """添加新标签"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 获取或创建标签
        tag = self.tag_controller.get_or_create_tag(tag_name)
        
        # 如果标签已在列表中，选中它
        if tag.id in self.tag_map:
            self.tag_map[tag.id].setSelected(True)
        else:
            # 添加到列表并选中
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            item.setSelected(True)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
        
        # 清空输入框
        self.new_tag_edit.clear()
    
    def get_task_data(self):
        """获取表单数据
        
        Returns:
            包含任务数据的字典，如果标题为空则返回None
        """
        title = self.title_edit.text().strip()
        if not title:
            return None
            
        # 从标题中提取标签
        title, tag_in_title = self.task_controller.extract_tag(title)
        
        # 获取选中的标签ID
        selected_tags = []
        for item in self.tag_list.selectedItems():
            tag_id = item.data(Qt.UserRole)
            selected_tags.append(tag_id)
            
        # 如果标题中有标签，添加到选中的标签列表
        if tag_in_title:
            tag = self.tag_controller.get_or_create_tag(tag_in_title)
            if tag.id not in selected_tags:
                selected_tags.append(tag.id)
                
        # 获取截止日期
        due_date_str = self.date_display.text()
        due_date = None
        if due_date_str and due_date_str != "无截止日期":
            # QDate.fromString 如果格式不匹配会返回一个无效的QDate，我们需要检查
            parsed_date = QDate.fromString(due_date_str, "yyyy-MM-dd")
            if parsed_date.isValid():
                 due_date = parsed_date.toString("yyyy-MM-dd")

        # 获取优先级
        priority = self.priority_combo.currentData()
        
        return {
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "tag_ids": selected_tags
        }


class TagSelectionDialog(QDialog):
    """标签选择对话框"""
    
    def __init__(self, tag_controller, selected_tag_ids=None, parent=None):
        """初始化对话框
        
        Args:
            tag_controller: 标签控制器
            selected_tag_ids: 已选中的标签ID列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.tag_controller = tag_controller
        self.selected_tag_ids = selected_tag_ids or []
        self.setWindowTitle("选择标签")
        self.setMinimumWidth(300)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标签列表
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.tag_list)
        
        # 添加新标签区域
        new_tag_layout = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("输入新标签")
        self.add_tag_btn = QPushButton("+")
        self.add_tag_btn.setMaximumWidth(30)
        new_tag_layout.addWidget(self.new_tag_edit)
        new_tag_layout.addWidget(self.add_tag_btn)
        layout.addLayout(new_tag_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # 加载标签并选中已选标签
        self.tag_map = {}
        for tag in self.tag_controller.get_all_tags():
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
            
            # 如果标签已经选中，则选中它
            if tag.id in self.selected_tag_ids:
                item.setSelected(True)
        
        # 连接信号
        self.add_tag_btn.clicked.connect(self._add_new_tag)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
    
    def _add_new_tag(self):
        """添加新标签"""
        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return
            
        # 获取或创建标签
        tag = self.tag_controller.get_or_create_tag(tag_name)
        
        # 如果标签已在列表中，选中它
        if tag.id in self.tag_map:
            self.tag_map[tag.id].setSelected(True)
        else:
            # 添加到列表并选中
            item = QListWidgetItem(tag.tag)
            item.setData(Qt.UserRole, tag.id)
            item.setSelected(True)
            self.tag_list.addItem(item)
            self.tag_map[tag.id] = item
        
        # 清空输入框
        self.new_tag_edit.clear()
    
    def get_selected_tag_ids(self):
        """获取选中的标签ID列表
        
        Returns:
            标签ID列表
        """
        selected_tags = []
        for item in self.tag_list.selectedItems():
            tag_id = item.data(Qt.UserRole)
            selected_tags.append(tag_id)
        return selected_tags


class TaskTab(QWidget):
    """任务标签页"""
    
    # 定义信号
    task_changed = Signal()
    
    def __init__(self, task_controller, tag_controller, parent=None):
        """初始化标签页
        
        Args:
            task_controller: 任务控制器
            tag_controller: 标签控制器
            parent: 父窗口
        """
        super().__init__(parent)
        self.task_controller = task_controller
        self.tag_controller = tag_controller
        self.selected_tags_for_new_task = []
        self._setup_ui()
        self.load_tasks()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 输入行
        input_row = QHBoxLayout()
        self.new_title_edit = QLineEdit()
        self.new_title_edit.setPlaceholderText("添加新任务")
        
        # 新的日期选择UI (替换 QDateEdit)
        self.new_date_display = QLineEdit()
        self.new_date_display.setPlaceholderText("无截止日期")
        self.new_date_display.setReadOnly(True)
        self.new_date_button = QPushButton("📅")
        self.new_date_button.setToolTip("选择截止日期")
        self.new_date_button.clicked.connect(self._open_add_task_calendar_dialog)
        
        # 新增：优先级选择下拉框
        self.priority_combo_new_task = QComboBox()
        self.priority_combo_new_task.addItem("无", Priority.NONE)
        self.priority_combo_new_task.addItem("低", Priority.LOW)
        self.priority_combo_new_task.addItem("中", Priority.MEDIUM)
        self.priority_combo_new_task.addItem("高", Priority.HIGH)
        
        self.tag_btn = QPushButton("选择标签")
        
        add_btn = QPushButton("添加")

        input_row.addWidget(self.new_title_edit)
        input_row.addWidget(self.new_date_display)
        input_row.addWidget(self.new_date_button)
        input_row.addWidget(self.priority_combo_new_task)
        input_row.addWidget(self.tag_btn)
        input_row.addWidget(add_btn)
        
        layout.addLayout(input_row)
        
        # 任务表格
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["完成", "任务", "截止日期", "优先级", "标签", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # 连接信号
        add_btn.clicked.connect(self.add_task)
        self.tag_btn.clicked.connect(self.select_tags)
        self.table.cellChanged.connect(self.handle_cell_changed)
        self.table.itemSelectionChanged.connect(self._on_task_selection_changed)

    def select_tags(self):
        """打开标签选择对话框"""
        dialog = TagSelectionDialog(
            self.tag_controller,
            self.selected_tags_for_new_task,
            self
        )
        
        if dialog.exec() == QDialog.Accepted:
            # 获取选中的标签
            self.selected_tags_for_new_task = dialog.get_selected_tag_ids()
            
            # 更新标签按钮文本
            self._update_tag_button_text()

    def _update_tag_button_text(self):
        """更新标签按钮文本"""
        if not self.selected_tags_for_new_task:
            self.tag_btn.setText("选择标签")
            return
            
        # 获取所有选中标签的名称
        tag_names = []
        for tag_id in self.selected_tags_for_new_task:
            tag = self.tag_controller.get_tag_by_id(tag_id)
            if tag:
                tag_names.append(tag.tag)
        
        # 如果标签太多，只显示前几个
        if len(tag_names) <= 2:
            self.tag_btn.setText(", ".join(tag_names))
        else:
            self.tag_btn.setText(f"{tag_names[0]}, {tag_names[1]}... (+{len(tag_names)-2})")
    
    def load_tasks(self):
        """加载所有任务"""
        self.table.setRowCount(0)
        
        for task in self.task_controller.get_all_tasks():
            self._add_task_to_table(task)
    
    def _add_task_to_table(self, task):
        """将任务添加到表格
        
        Args:
            task: 任务对象
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 完成复选框
        chk_item = QTableWidgetItem()
        chk_item.setFlags(chk_item.flags() | Qt.ItemIsUserCheckable)
        chk_item.setCheckState(Qt.Checked if task.completed else Qt.Unchecked)
        chk_item.setData(Qt.UserRole, task.id)
        chk_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, chk_item)
        
        # 标题
        title_item = QTableWidgetItem(task.title)
        title_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, title_item)
        
        # 截止日期
        due_date_display_str = "无截止日期" # Default to show if effectively null
        if task.due_date is not None:
            is_1752_date = (task.due_date.year == 1752 and
                            task.due_date.month == 9 and
                            task.due_date.day == 14)
            if not is_1752_date:
                # It's a valid date and not the 1752 placeholder, so format it
                due_date_display_str = task.due_date.strftime("%Y-%m-%d")
        # If task.due_date is None, or if it's the 1752 date, due_date_display_str remains "无截止日期"
        
        due_date_item = QTableWidgetItem(due_date_display_str)
        due_date_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, due_date_item)
        
        # 优先级
        priority_item = QTableWidgetItem(task.get_priority_name())
        priority_item.setTextAlignment(Qt.AlignCenter)
        
        # 设置优先级单元格颜色
        if task.priority > Priority.NONE:
            color = task.get_priority_color()
            priority_item.setForeground(QColor("white"))
            priority_item.setBackground(QColor(color))
        else:
            priority_item.setForeground(QColor("gray"))
        self.table.setItem(row, 3, priority_item)
        
        # 标签
        tag_text = ", ".join([tag.tag for tag in task.tags]) if task.tags else ""
        tag_item = QTableWidgetItem(tag_text)
        tag_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, tag_item)
        
        # 操作按钮
        action_widget = QWidget()
        hl = QHBoxLayout(action_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        edit_btn = QPushButton("编辑")
        delete_btn = QPushButton("删除")
        hl.addStretch(1)
        hl.addWidget(edit_btn)
        hl.addWidget(delete_btn)
        hl.addStretch(1)
        self.table.setCellWidget(row, 5, action_widget)
        
        # 连接信号
        edit_btn.clicked.connect(lambda _, tid=task.id: self.edit_task(tid))
        delete_btn.clicked.connect(lambda _, tid=task.id: self.delete_task(tid))
        
        # 如果任务已完成，添加删除线
        if task.completed:
            font = title_item.font()
            font.setStrikeOut(True)
            title_item.setFont(font)
    
    def _open_add_task_calendar_dialog(self):
        # 标记是否已选择"无截止日期"
        no_due_date_selected = [False]  # 使用列表以便在lambda中可以修改
        dialog = QDialog(self)
        dialog.setWindowTitle("选择截止日期")
        layout = QVBoxLayout(dialog)

        calendar = QCalendarWidget(dialog)
        calendar.setMinimumDate(QDate.currentDate()) # 只能选择当天及以后
        if self.new_date_display.text() != "无截止日期" and self.new_date_display.text():
            try:
                current_date = QDate.fromString(self.new_date_display.text(), "yyyy-MM-dd")
                if current_date.isValid():
                    calendar.setSelectedDate(current_date)
            except Exception:
                pass # 如果解析失败，则不设置日期

        layout.addWidget(calendar)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset, dialog)
        clear_button = button_box.button(QDialogButtonBox.Reset)
        if clear_button: 
            clear_button.setText("无截止日期")
            clear_button.clicked.connect(lambda: self._set_no_due_date(dialog, no_due_date_selected))
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        if not clear_button:
            manual_clear_button = QPushButton("无截止日期")
            manual_clear_button.clicked.connect(lambda: self._set_no_due_date(dialog, no_due_date_selected))
            button_box.addButton(manual_clear_button, QDialogButtonBox.ActionRole)

        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec():
            if no_due_date_selected[0]:
                # 已经在_set_no_due_date中设置为"无截止日期"
                pass
            else:
                selected_date = calendar.selectedDate()
                self.new_date_display.setText(selected_date.toString("yyyy-MM-dd"))

    def _set_no_due_date(self, dialog, no_due_date_flag):
        """设置为无截止日期并关闭对话框"""
        self.new_date_display.setText("无截止日期")
        no_due_date_flag[0] = True
        dialog.accept()
        
    def add_task(self):
        """添加新任务"""
        title = self.new_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "警告", "任务标题不能为空！")
            return

        due_date_str = self.new_date_display.text()
        due_date = None
        if due_date_str and due_date_str != "无截止日期":
            parsed_date = QDate.fromString(due_date_str, "yyyy-MM-dd")
            if parsed_date.isValid():
                due_date = parsed_date.toString("yyyy-MM-dd")
            else: # 如果解析后日期无效，也视为无截止日期或给出警告
                # QMessageBox.warning(self, "警告", f"日期格式不正确: {due_date_str}")
                due_date = None # 或者保持为 None
        
        priority_str = self.priority_combo_new_task.currentText() # 假设有这样一个优先级选择器
        priority = Priority.NONE # 默认值
        if priority_str == "高":
            priority = Priority.HIGH
        elif priority_str == "中":
            priority = Priority.MEDIUM
        elif priority_str == "低":
            priority = Priority.LOW

        # task_id, title, due_date, priority, completed, tags, created_at, updated_at
        task_data = {
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "tag_ids": self.selected_tags_for_new_task
        }
        
        new_task = self.task_controller.create_task(**task_data)
        
        if new_task:
            self.load_tasks()
            self.new_title_edit.clear()
            self.new_date_display.setText("无截止日期") # 清空日期显示
            self.selected_tags_for_new_task = [] # 清空已选标签
            self.tag_btn.setText("选择标签")
            QMessageBox.information(self, "成功", "任务已添加！")
            self.task_changed.emit()
        else:
            QMessageBox.critical(self, "错误", "添加任务失败！")

    def edit_task(self, task_id):
        task = self.task_controller.get_task_by_id(task_id)
        if task:
            dialog = TaskEditDialog(self.task_controller, self.tag_controller, task, self)
            if dialog.exec() == QDialog.Accepted:
                task_data = dialog.get_task_data() # 修正方法名
                if task_data:
                    self.task_controller.update_task(task_id, task_data) # 修正参数传递
                    self.load_tasks()
                    self.task_changed.emit()
                else:
                    QMessageBox.warning(self, "警告", "任务标题不能为空！")
            else:
                pass # 用户取消了编辑

    def delete_task(self, task_id):
        reply = QMessageBox.question(self, "确认", "确定删除该任务吗？")
        if reply == QMessageBox.Yes:
            self.task_controller.delete_task(task_id)
            self.load_tasks()
            self.task_changed.emit()
        else:
            pass # 用户取消了删除

    def handle_cell_changed(self, row, column):
        """处理单元格变更，主要用于任务完成状态切换"""
        if column == 0: # 第一列是复选框
            item = self.table.item(row, column)
            if not item:
                return
            
            task_id = item.data(Qt.UserRole) # 假设任务ID存储在UserRole中
            if task_id is None:
                return # 没有关联的任务ID
            
            task = self.task_controller.get_task_by_id(task_id)
            if not task:
                return

            new_completed_status = item.checkState() == Qt.CheckState.Checked
            
            # 调用控制器更新任务状态
            # 假设 update_task 可以处理 'completed' 字段
            updated_task = self.task_controller.update_task(task_id, {"completed": new_completed_status})

            if updated_task:
                # 更新UI上的删除线
                title_item = self.table.item(row, 1) # 假设第二列是标题
                if title_item:
                    font = title_item.font()
                    font.setStrikeOut(new_completed_status)
                    title_item.setFont(font)
                
                self.task_changed.emit() # 发出信号通知其他组件（如图表）更新
            else:
                # 可以添加错误处理，例如弹窗提示更新失败
                QMessageBox.warning(self, "错误", f"更新任务 {task.title} 状态失败。")
                # 恢复复选框状态以匹配实际数据
                item.setCheckState(Qt.CheckState.Checked if task.completed else Qt.CheckState.Unchecked)

    def _on_task_selection_changed(self):
        """处理任务选择变化"""
        pass
