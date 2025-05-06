// 获取模态框元素
const modal = document.getElementById('editModal');
const closeBtn = document.querySelector('.close');
const saveTaskBtn = document.getElementById('saveTaskBtn');
const cancelEditBtn = document.getElementById('cancelEditBtn');
let currentEditingTaskId = null;

// 初始化日期选择器和标签选择器的点击处理
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('taskDueDate');
    const dateContainer = document.querySelector('.date-input-container');

    // 阻止日期选择器的点击事件冒泡
    dateInput.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // 点击容器时手动触发日期选择器
    dateContainer.addEventListener('click', function(e) {
        if (e.target === dateContainer) {
            dateInput.showPicker();
        }
    });

    // 初始化获取标签列表
    fetchTags();
});

// 获取所有标签
async function fetchTags() {
    const response = await fetch('/api/tags');
    const tags = await response.json();
    updateTagSelects(tags);
}

// 更新所有标签选择框
function updateTagSelects(tags) {
    const selects = [
        document.getElementById('taskTag'),
        document.getElementById('editTaskTag')
    ];
    
    selects.forEach(select => {
        const currentValue = select.value;
        select.innerHTML = '<option value="">无标签</option>';
        tags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag.id;
            option.textContent = tag.tag;
            select.appendChild(option);
        });
        select.value = currentValue;
    });
}

// 关闭模态框
function closeModal() {
    modal.style.display = 'none';
}

// 打开模态框
function openModal() {
    modal.style.display = 'block';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    if (event.target === modal) {
        closeModal();
    }
}

// 关闭按钮事件
closeBtn.onclick = closeModal;
cancelEditBtn.onclick = closeModal;

// 获取所有任务
async function fetchTasks() {
    const response = await fetch('/api/tasks');
    const tasks = await response.json();
    renderTasks(tasks);
}

// 渲染任务列表
function renderTasks(tasks) {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item ${task.completed ? 'completed' : ''}`;
        taskElement.innerHTML = `
            <input type="checkbox" ${task.completed ? 'checked' : ''} 
                   onchange="toggleTask(${task.id}, this.checked)">
            <div class="task-info">
                <span class="task-content">
                    ${task.title}
                </span>
                ${task.due_date ? `<span class="task-due-date">截止日期: ${task.due_date}</span>` : ''}
            </div>
            <div class="task-actions">
                <button onclick="showEditModal(${task.id}, '${task.title}', '${task.due_date || ''}', ${task.tag_id || 'null'})">编辑</button>
                <button class="delete-btn" onclick="deleteTask(${task.id})">删除</button>
            </div>
        `;
        taskList.appendChild(taskElement);
    });
}

// 添加新任务
async function addTask() {
    const input = document.getElementById('newTask');
    const dateInput = document.getElementById('taskDueDate');
    const tagSelect = document.getElementById('taskTag');
    let title = input.value.trim();
    const dueDate = dateInput.value;
    
    if (!title) return;
    
    // 如果选择了标签，添加到标题末尾
    if (tagSelect.value) {
        const tagOption = tagSelect.options[tagSelect.selectedIndex];
        title = `${title} #${tagOption.textContent}`;
    }
    
    const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            title,
            due_date: dueDate || null
        })
    });
    
    if (response.ok) {
        input.value = '';
        dateInput.value = '';
        tagSelect.value = '';
        fetchTasks();
    }
}

// 显示编辑模态框
function showEditModal(taskId, title, dueDate, tagId) {
    currentEditingTaskId = taskId;
    document.getElementById('editTaskTitle').value = title;
    document.getElementById('editTaskDueDate').value = dueDate;
    document.getElementById('editTaskTag').value = '';  // 重置标签选择框
    openModal();
}

// 保存编辑的任务
saveTaskBtn.onclick = async function() {
    if (!currentEditingTaskId) return;
    
    const titleInput = document.getElementById('editTaskTitle');
    const dueDateInput = document.getElementById('editTaskDueDate');
    const tagSelect = document.getElementById('editTaskTag');
    let title = titleInput.value.trim();
    
    if (!title) return;
    
    // 如果选择了新标签，添加到标题末尾
    if (tagSelect.value) {
        const tagOption = tagSelect.options[tagSelect.selectedIndex];
        title = `${title} #${tagOption.textContent}`;
        tagSelect.value = ''; // 重置标签选择
    }
    
    const response = await fetch(`/api/tasks/${currentEditingTaskId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            title,
            due_date: dueDateInput.value || null
        })
    });
    
    if (response.ok) {
        closeModal();
        fetchTasks();
    }
}

// 切换任务状态
async function toggleTask(taskId, completed) {
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ completed })
    });
    
    if (response.ok) {
        fetchTasks();
    }
}

// 删除任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？')) return;
    
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
    });
    
    if (response.ok) {
        fetchTasks();
    }
}

// 页面加载时获取任务列表
document.addEventListener('DOMContentLoaded', fetchTasks);

// 为输入框添加回车键监听
document.getElementById('newTask').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        addTask();
    }
});
