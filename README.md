# TaskMoment

TaskMoment 是一款简洁高效的在线任务管理工具，旨在帮助用户轻松记录、跟踪并高效管理日常任务。通过清晰的任务列表、智能提醒和实时进度更新，TaskMoment 帮助用户合理规划时间，提升个人和团队的工作效率。无论是个人待办事项，还是团队协作任务，TaskMoment 都能提供便捷的解决方案。

## 主要功能

- **创建、编辑和删除任务**
- **设置任务提醒和截止日期**
- **任务优先级和分类管理**
- **支持跨设备同步，随时随地管理任务**

## TODO

- [x] 创建一个仓库
- [ ] 添加用户登录和注册功能
- [ ] 完善数据库设计
- [ ] 实现前端界面
- [ ] 添加任务管理功能

## 环境搭建

1. 创建并激活 Python 环境
```bash
conda create -n TaskMoment python=3.12 -y
conda activate TaskMoment
```

2. 克隆项目
```bash
git clone https://github.com/boomytc/TaskMoment.git
cd TaskMoment
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 数据库配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
DB_HOST=your_database_host
DB_PORT=your_database_port
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
```

## 项目结构

```
TaskMoment/
│
├── demo/                  # 示例代码
│   └── test/             
│       ├── connect/      # 数据库连接示例
│       ├── insert/       # 数据插入示例
│       └── delete/       # 数据删除示例
│
├── requirements.txt      # 项目依赖
└── README.md            # 项目说明文档



