import uuid
import time
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class TaskStatusModel(BaseModel):
    id: str
    name: str
    status: str
    progress: float
    logs: List[str]
    result: Optional[Dict[str, Any]] = None
    elapsed: float

class BackgroundTask:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.status = "running"  # running, success, failed
        self.progress = 0.0
        self.logs: List[str] = []
        self.result: Optional[Any] = None
        self.created_at = time.time()
        self.updated_at = time.time()
        self._lock = threading.Lock()

    def log(self, message: str):
        with self._lock:
            t_str = time.strftime("%H:%M:%S", time.localtime())
            self.logs.append(f"[{t_str}] {message}")
            self.updated_at = time.time()

    def update_progress(self, progress: float):
        with self._lock:
            self.progress = min(max(progress, 0.0), 1.0)
            self.updated_at = time.time()

    def set_success(self, result: Any = None):
        with self._lock:
            self.status = "success"
            self.progress = 1.0
            self.result = result
            self.updated_at = time.time()

    def set_failed(self, error_message: str):
        with self._lock:
            self.status = "failed"
            t_str = time.strftime("%H:%M:%S", time.localtime())
            self.logs.append(f"[{t_str}] ERROR: {error_message}")
            self.updated_at = time.time()

    def to_model(self) -> TaskStatusModel:
        with self._lock:
            res_dict = None
            if isinstance(self.result, dict):
                res_dict = self.result
            elif hasattr(self.result, "model_dump"):
                try:
                    res_dict = self.result.model_dump()
                except Exception:
                    pass
            elif hasattr(self.result, "__dict__"):
                try:
                    res_dict = self.result.__dict__
                except Exception:
                    pass

            return TaskStatusModel(
                id=self.id,
                name=self.name,
                status=self.status,
                progress=self.progress,
                logs=list(self.logs),
                result=res_dict,
                elapsed=round(time.time() - self.created_at, 2)
            )

class TaskRegistry:
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self._lock = threading.Lock()

    def create_task(self, name: str) -> BackgroundTask:
        task = BackgroundTask(name)
        with self._lock:
            self.tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        with self._lock:
            return self.tasks.get(task_id)

task_registry = TaskRegistry()
