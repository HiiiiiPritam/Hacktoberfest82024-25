import logging
from abc import ABC, abstractmethod
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_task import WorkerTask

logger = logging.getLogger(__name__)

class BaseWorker(WorkerInterface, ABC):
    def __init__(self, task_def_name: str, poll_interval: float = 1.0):
        super().__init__(task_definition_name=task_def_name)
        self.task_def_name = task_def_name
        self.poll_interval = poll_interval
        # Initialize required attributes for Conductor
        self._domain = None
        self._task_definition_name = task_def_name
        self._poll_interval = poll_interval
        
    def get_task_definition_name(self) -> str:
        """Return the task definition name"""
        return self.task_def_name
        
    def get_poll_interval_in_seconds(self) -> float:
        """Return polling interval in seconds"""
        return self.poll_interval
        
    def get_domain(self) -> str:
        """Return worker domain"""
        return self._domain
        
    def execute(self, task: WorkerTask) -> WorkerTask:
        """Execute the task - calls the abstract process_task method"""
        try:
            logger.info(f"Processing task: {self.task_def_name}, task_id: {task.task_id}")
            
            # Extract input data
            input_data = task.input_data if task.input_data else {}
            
            # Process the task
            result = self.process_task(input_data, task.task_id)
            
            # Set the result
            task.output_data = result
            task.status = "COMPLETED"
            
            logger.info(f"Task {self.task_def_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {self.task_def_name} failed: {str(e)}")
            task.output_data = {"error": str(e)}
            task.status = "FAILED"
            
        return task
        
    @abstractmethod
    def process_task(self, input_data: dict, task_id: str) -> dict:
        """Process the task - implement this in subclasses"""
        pass