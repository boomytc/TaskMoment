\
from PySide6.QtCore import QObject, Signal, QRunnable
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import case, desc, asc

from app.models.task import Task, Priority 
# Ensure Task.tags relationship is defined in app.models.task.py for selectinload to work
# from app.models.tag import Tag # Import if needed for other workers

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished:
        object data returned from processing, anything
    error:
        str error message
    """
    finished = Signal(object)
    error = Signal(str)
    # progress = Signal(int) # Example for progress reporting, if needed

class BaseWorker(QRunnable):
    """
    Base worker QRunnable.
    """
    def __init__(self, session_maker: sessionmaker, *args, **kwargs):
        super().__init__()
        self.session_maker = session_maker
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        # This method must be implemented by subclasses
        raise NotImplementedError("Subclasses must implement the run method.")

class GetAllTasksWorker(BaseWorker):
    """
    Worker to fetch all tasks from the database asynchronously.
    """
    def run(self):
        session = None
        try:
            session = self.session_maker()
            
            # This logic is similar to TaskController.get_all_tasks
            # It's placed here to be executed in the worker thread.
            due_date_case = case(
                (Task.due_date == None, 1),  # Null due dates appear after dated tasks
                else_=0
            )
            completed_case = case(
                (Task.completed == True, 1),  # Completed tasks appear after incomplete tasks
                else_=0
            )
            
            # Eagerly load tags to prevent further queries on the main thread
            # when accessing task.tags later in the UI update.
            tasks = session.query(Task).options(
                selectinload(Task.tags) 
            ).order_by(
                completed_case,
                due_date_case,
                asc(Task.due_date),
                desc(Task.priority),
                desc(Task.created_at)
            ).all()
            
            self.signals.finished.emit(tasks)
        except Exception as e:
            # Consider more detailed error logging or specific exception handling
            # import traceback
            # self.signals.error.emit(f"Error fetching tasks: {str(e)}\\n{traceback.format_exc()}")
            self.signals.error.emit(f"获取任务时出错: {str(e)}")
        finally:
            if session:
                session.close()

# Future workers (examples):
# class CreateTaskWorker(BaseWorker): ...
# class UpdateTaskWorker(BaseWorker): ...
# class DeleteTaskWorker(BaseWorker): ...
# class GetTaskByIdWorker(BaseWorker): ...

# class GetAllTagsWorker(BaseWorker): ...
# class CreateTagWorker(BaseWorker): ...
# etc.
