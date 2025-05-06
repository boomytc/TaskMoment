from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import webbrowser
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50), nullable=False, unique=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tag': self.tag
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=True)
    tag = db.relationship('Tag', backref=db.backref('tasks', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'tag': self.tag.tag if self.tag else None,
            'tag_id': self.tag_id
        }

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def extract_tag(title):
    """从标题中提取标签，格式为 任务内容 #标签"""
    words = title.split()
    tag_name = None
    new_title = []
    
    for word in words:
        if word.startswith('#') and len(word) > 1:
            tag_name = word[1:]  # 去掉#号
        else:
            new_title.append(word)
    
    return ' '.join(new_title), tag_name

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    response_data = []
    for task in tasks:
        task_data = task.to_dict()
        if task.tag:
            task_data['title'] = f"{task.title} #{task.tag.tag}"
        response_data.append(task_data)
    return jsonify(response_data)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    title = data['title']
    title, tag_name = extract_tag(title)
    
    tag_id = None
    if tag_name:
        # 查找或创建标签
        tag = Tag.query.filter_by(tag=tag_name).first()
        if not tag:
            tag = Tag(tag=tag_name)
            db.session.add(tag)
            db.session.commit()
        tag_id = tag.id
    
    due_date = parse_date(data.get('due_date'))
    task = Task(
        title=title,
        due_date=due_date,
        tag_id=tag_id
    )
    db.session.add(task)
    db.session.commit()
    
    # 在返回数据中添加完整的标题（包含标签）
    response_data = task.to_dict()
    if tag_name:
        response_data['title'] = f"{title} #{tag_name}"
    return jsonify(response_data)

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if 'title' in data:
        title = data['title']
        title, tag_name = extract_tag(title)
        task.title = title
        
        if tag_name:
            # 查找或创建标签
            tag = Tag.query.filter_by(tag=tag_name).first()
            if not tag:
                tag = Tag(tag=tag_name)
                db.session.add(tag)
                db.session.commit()
            task.tag_id = tag.id
        else:
            task.tag_id = None
            
    if 'completed' in data:
        task.completed = data['completed']
    if 'due_date' in data:
        task.due_date = parse_date(data['due_date'])
    
    db.session.commit()
    
    # 在返回数据中添加完整的标题（包含标签）
    response_data = task.to_dict()
    if task.tag:
        response_data['title'] = f"{task.title} #{task.tag.tag}"
    return jsonify(response_data)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

@app.route('/api/tags', methods=['GET'])
def get_tags():
    tags = Tag.query.all()
    return jsonify([tag.to_dict() for tag in tags])

@app.route('/api/tags', methods=['POST'])
def create_tag():
    data = request.get_json()
    if not data or 'tag' not in data:
        return jsonify({'error': 'Tag name is required'}), 400
    
    tag_name = data['tag'].strip()
    if not tag_name:
        return jsonify({'error': 'Tag name cannot be empty'}), 400
    
    # 检查标签是否已存在
    existing_tag = Tag.query.filter_by(tag=tag_name).first()
    if existing_tag:
        return jsonify(existing_tag.to_dict())
    
    tag = Tag(tag=tag_name)
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag.to_dict())

if __name__ == '__main__':
    # 在1秒后尝试打开浏览器
    threading.Timer(1, lambda: webbrowser.open_new("http://127.0.0.1:5000/")).start()
    app.run(debug=True, host='127.0.0.1', port=5000)
