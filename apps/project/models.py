from django.db import models
from django.db.models import Case, When, F, Sum
from django.utils import timezone
from apps.core.mixins import (
    LogicalDeletable, Permalinkable, Timestampable, SingletonMixin, Authorable, NonSequentialIdentifierMixin,
    LogicalDeletableQuerySet
)


class ProjectSetting(Timestampable, SingletonMixin, models.Model):
    concurrent_tasks = models.BooleanField(default=False)

    class Meta:
        db_table = 'project_setting'


class ProjectQuerySet(LogicalDeletableQuerySet, models.QuerySet):
    def user_projects(self, user):
        return self.filter(created_by=user)


class Project(
    NonSequentialIdentifierMixin,
    LogicalDeletable,
    Timestampable,
    Permalinkable,
    Authorable,
    models.Model):
    title = models.CharField(max_length=255)
    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ('-created_at', )

    def __str__(self):
        return self.title

    def get_all_tasks_with_duration(self):
        return self.tasks.annotate(duration=Sum(F("time_entries__end_datetime") - F("time_entries__created_at")))

    def has_any_running_task(self):
        """Get all task time_entries of a project and check if any of them is running or not
        
        Also you can do that without looping through all tasks to be more efficient, but this is just a
        demostration of using `prefetch_related()` function to solve n+1 problem
        """
        tasks = self.tasks.prefetch_related('time_entries').all()
        return any((task.is_running() for task in tasks))

    def stop_all_tasks(self):
        return TaskTimeEntry.objects.filter(task__project=self).update(end_datetime=timezone.now())


class TaskQuerySet(LogicalDeletableQuerySet, models.QuerySet):
    def user_running_tasks(self, user):
        return self.filter(project__created_by=user, time_entries__end_datetime__isnull=True)

    def user_finished_tasks(self, user):
        return self.filter(project__created_by=user, time_entries__end_datetime__isnull=False)

    
class Task(Timestampable, NonSequentialIdentifierMixin, models.Model):
    title = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    objects = TaskQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_total_spent_time(self, include_running_task=False):
        default = timezone.now() if include_running_task else F("created_at")
        delta = self.time_entries.annotate(
            end=Case(
                When(end_datetime__isnull=False, then=F("end_datetime")),
                default=default
            ),
            duration=F("end") - F("created_at")
        ).aggregate(s=Sum("duration"))["s"]
        return delta.seconds if delta else 0

    def is_running(self):
        return self.time_entries.filter(end_datetime__isnull=True).exists()

    def start(self):
        """Start a task by creating a new time entry
        
        You cannot have a task with more than one time entries that have end_datetime=None. That means, your task
        already is running.
        """
        if self.is_running():
            return
        TaskTimeEntry.objects.create(task=self)

    def stop(self):
        """Stop a task by updating its time_entry's end_datetime attribute
        
        If there isn't any running task, we do nothing
        """
        self.time_entries.filter(end_datetime__isnull=True).update(end_datetime=timezone.now())


class TaskTimeEntry(Timestampable, NonSequentialIdentifierMixin, models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    end_datetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'task_time_entry'
        ordering = ('-created_at', )

    def __str__(self):
        return f"{self.task.title}: {self.duration_in_sec} sec(s)"

    @property
    def start_datetime(self):
        return self.created_at

    @property
    def duration_in_sec(self):
        end_datetime = self.end_datetime or timezone.now()
        return (end_datetime - self.start_datetime).seconds

    def is_finished(self):
        return not self.end_datetime == None

    def finish(self, commit=True):
        self.end_datetime = timezone.now()
        if commit:
            self.save()