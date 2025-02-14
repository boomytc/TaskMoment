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
            <span class="task-content">${task.title}</span>
            <div class="task-actions">
                <button onclick="editTask(${task.id}, '${task.title}')">编辑</button>
                <button class="delete-btn" onclick="deleteTask(${task.id})">删除</button>
            </div>
        `;
        taskList.appendChild(taskElement);
    });
}

// 添加新任务
async function addTask() {
    const input = document.getElementById('newTask');
    const title = input.value.trim();
    
    if (!title) return;
    
    const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title })
    });
    
    if (response.ok) {
        input.value = '';
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

// 编辑任务
async function editTask(taskId, currentTitle) {
    const newTitle = prompt('编辑任务:', currentTitle);
    
    if (newTitle === null || newTitle.trim() === '') return;
    
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: newTitle })
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
