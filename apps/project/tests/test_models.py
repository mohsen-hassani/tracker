from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from ..models import ProjectSetting, Project, Task, TaskTimeEntry
from apps.user.models import User


class ProjectSettingTests(TestCase):
    def test_setting_is_singleton(self):
        cache.delete(ProjectSetting.__name__)
        self.assertEqual(ProjectSetting.objects.count(), 0)
        setting_1 = ProjectSetting.load()
        self.assertEqual(ProjectSetting.objects.count(), 1)
        setting_2 = ProjectSetting.load()
        self.assertEqual(ProjectSetting.objects.count(), 1)
        setting_3 = ProjectSetting.objects.first()
        self.assertEqual(setting_1.id, setting_2.id)
        self.assertEqual(setting_1.id, setting_3.id)

    def test_cannot_delete_setting(self):
        cache.delete(ProjectSetting.__name__)
        with self.assertRaises(AttributeError):
            setting = ProjectSetting.load()
            setting.delete()
        
    def test_update_dont_change_pk(self):
        cache.delete(ProjectSetting.__name__)
        setting = ProjectSetting.load()
        setting.concurrent_tasks = True
        setting.save()
        self.assertEqual(setting.pk, 1)
        setting.pk = 2 
        setting.save()
        self.assertEqual(setting.pk, 1)

        
class ProjectTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create(email="dummy_email_a@gmail.com")
        self.user_b = User.objects.create(email="dummy_email_b@gmail.com")
        self.project_a = Project.objects.create(title="Project A", created_by=self.user_a)
        self.project_b = Project.objects.create(title="Project B", created_by=self.user_a)
        self.project_c = Project.objects.create(title="Project C", created_by=self.user_b)

    def test_delete_project(self):
        self.assertFalse(self.project_a.is_deleted)
        self.project_a.delete()
        self.assertTrue(self.project_a.is_deleted)
        self.assertIn(self.project_a, Project.objects.deleted())
        self.assertNotIn(self.project_a, Project.objects.non_deleted())
        self.project_a.restore()
        self.assertFalse(self.project_a.is_deleted)
        self.assertNotIn(self.project_a, Project.objects.deleted())
        self.assertIn(self.project_a, Project.objects.non_deleted())

    def test_user_projects(self):
        self.assertIn(self.project_a, Project.objects.user_projects(self.user_a))
        self.assertIn(self.project_b, Project.objects.user_projects(self.user_a))
        self.assertNotIn(self.project_c, Project.objects.user_projects(self.user_a))

    def test_has_any_running_task_return_true_when_there_is_one(self):
        task = Task.objects.create(title="Task", project=self.project_a)
        task.start()
        self.assertTrue(self.project_a.has_any_running_task())

    def test_has_any_running_task_return_false_when_there_is_no_running_task(self):
        self.assertFalse(self.project_a.has_any_running_task())

    def test_stop_all_tasks_stops_tasks(self):
        task_a = Task.objects.create(title="Task", project=self.project_a)
        task_b = Task.objects.create(title="Task", project=self.project_a)
        task_a.start()
        task_b.start()
        self.project_a.stop_all_tasks()
        self.assertFalse(self.project_a.has_any_running_task())

    def test_stop_all_tasks_return_number_of_stopped_tasks(self):
        task_a = Task.objects.create(title="Task", project=self.project_a)
        task_b = Task.objects.create(title="Task", project=self.project_a)
        task_c = Task.objects.create(title="Task", project=self.project_a)
        task_a.start()
        task_b.start()
        stopped_tasks = self.project_a.stop_all_tasks()
        self.assertEqual(stopped_tasks, 2)

    def test_stop_all_tasks_dont_stop_other_project_tasks(self):
        task_a = Task.objects.create(title="Task", project=self.project_a)
        task_b = Task.objects.create(title="Task", project=self.project_a)
        task_c = Task.objects.create(title="Task", project=self.project_b)
        task_a.start()
        task_b.start()
        task_c.start()
        self.project_a.stop_all_tasks()
        self.assertFalse(self.project_a.has_any_running_task())
        self.assertTrue(self.project_b.has_any_running_task())


class TaskTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create(email="dummy_email_a@gmail.com")
        self.user_b = User.objects.create(email="dummy_email_b@gmail.com")
        self.project = Project.objects.create(title="Project A", created_by=self.user_a)
        self.task = Task.objects.create(title="Task A", project=self.project)

    def test_start_stop_task(self):
        self.assertFalse(self.task.is_running())
        self.task.start()
        self.assertTrue(self.task.is_running())
        self.task.stop()
        self.assertFalse(self.task.is_running())

    def test_user_tasks(self):
        user_running_tasks = Task.objects.user_running_tasks(self.user_a)
        self.assertIn(self.task, user_running_tasks)
        user_finished_tasks = Task.objects.user_finished_tasks(self.user_b)
        self.assertNotIn(self.task, user_finished_tasks)


    def test_get_spend_time_on_running_tasks_shouldnt_raise_error(self):
        self.task.start()
        self.task.get_total_spent_time()

    def test_get_spend_time_on_new_tasks_should_return_zero(self):
        self.assertEqual(self.task.get_total_spent_time(), 0)


    def test_spend_time_method(self):
        tte1 = TaskTimeEntry.objects.create(task=self.task)
        tte1.end_datetime = tte1.start_datetime + timedelta(seconds=10)
        tte1.save()
        self.assertEqual(self.task.get_total_spent_time(), 10)
        tte2 = TaskTimeEntry.objects.create(task=self.task)
        tte2.end_datetime = tte2.start_datetime + timedelta(seconds=20)
        tte2.save()
        self.assertEqual(self.task.get_total_spent_time(), 30)


    def test_start_task_creates_time_entry(self):
        self.assertEqual(self.task.time_entries.count(), 0)
        self.task.start()
        self.assertEqual(self.task.time_entries.count(), 1)
        self.task.stop()
        self.assertEqual(self.task.time_entries.count(), 1)
        self.task.start()
        self.assertEqual(self.task.time_entries.count(), 2)
        self.task.stop()
        self.assertEqual(self.task.time_entries.count(), 2)

    def test_get_all_tasks_with_duration(self):
        task_b = Task.objects.create(title="Task B", project=self.project)
        task_c = Task.objects.create(title="Task C", project=self.project)
        now = timezone.now()
        taa = TaskTimeEntry.objects.create(task=self.task)
        tab = TaskTimeEntry.objects.create(task=self.task)
        tac = TaskTimeEntry.objects.create(task=self.task)
        tba = TaskTimeEntry.objects.create(task=task_b)
        tca = TaskTimeEntry.objects.create(task=task_c)
        tcb = TaskTimeEntry.objects.create(task=task_c)
        taa.created_at = tab.created_at = tac.created_at = tba.created_at = tca.created_at = tcb.created_at = now
        taa.end_datetime = now + timedelta(seconds=20)
        tab.end_datetime = None
        tac.end_datetime = now + timedelta(seconds=10)
        tba.end_datetime = now + timedelta(seconds=20)
        tca.end_datetime = now + timedelta(seconds=5)
        tcb.end_datetime = now + timedelta(seconds=15)
        taa.save()
        tab.save()
        tac.save()
        tba.save()
        tca.save()
        tcb.save()
        ta, tb, tc = self.project.get_all_tasks_with_duration()
        self.assertEqual(ta.duration.seconds, 30)
        self.assertEqual(tb.duration.seconds, 20)
        self.assertEqual(tc.duration.seconds, 20)


class TaskTimeEntryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="dummy_email@gmail.com")
        self.project = Project.objects.create(title="Project A", created_by=self.user)
        self.task = Task.objects.create(title="Task A", project=self.project)
        self.tte = TaskTimeEntry.objects.create(task=self.task)

    def test_time_entry_finish_method(self):
        self.assertFalse(self.tte.is_finished())
        self.tte.finish(commit=False)
        self.assertTrue(self.tte.is_finished())
        self.tte.refresh_from_db()
        self.assertFalse(self.tte.is_finished())
        self.tte.finish()
        self.tte.refresh_from_db()
        self.assertTrue(self.tte.is_finished())

    def test_start_datetime_is_created_at(self):
        self.tte.finish()
        self.assertEqual(self.tte.created_at, self.tte.start_datetime)

