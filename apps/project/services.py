from apps.core.base import AbstractService
from .exceptions import NoRunningTaskFoundException, CuncurrentTaskException
from .models import Project, ProjectSetting


class StopAllTasksService(AbstractService):
    """Get a project as input and stop all task_time_entries related to that project
        Raise NoRunningTaskFoundException if all tasks are stopped
    """
    project = None

    def execute(self):
        proj: Project = self.project
        if not proj.has_any_running_task():
            raise NoRunningTaskFoundException()
        stopped_tasks = proj.stop_all_tasks()
        return stopped_tasks


class StartTaskService(AbstractService):
    task = None

    def execute(self):
        task = self.task
        setting = ProjectSetting.load()
        if setting.concurrent_tasks and task.project.has_any_running_task():
            raise CuncurrentTaskException()
        task.start()
