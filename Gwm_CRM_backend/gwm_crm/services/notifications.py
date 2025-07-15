from datetime import timedelta
from django.utils import timezone
from gwm_crm.models import Task, Meeting, Notification

def create_notifications():
    now = timezone.now()

    new_tasks = Task.objects.filter(
        created_at__gte=now - timedelta(minutes=10),
        assigned_to__isnull=False
    )

    for task in new_tasks:
        if not Notification.objects.filter(user=task.assigned_to, type='task_assigned', related_object_id=task.id).exists():
            Notification.objects.create(
                user=task.assigned_to,
                type='task_assigned',
                title='New Task Assigned',
                message=f"You have been assigned a task: {task.title}",
                related_object_id=task.id
            )

    soon = now + timedelta(hours=24)
    tasks_due = Task.objects.filter(due_datelte=soon, due_dategte=now, assigned_to__isnull=False)
    for task in tasks_due:
        if not Notification.objects.filter(user=task.assigned_to, type='task_due_soon', related_object_id=task.id).exists():
            Notification.objects.create(
                user=task.assigned_to,
                type='task_due_soon',
                title='Task Due Soon',
                message=f"The task '{task.title}' is due soon!",
                related_object_id=task.id
            )

    meetings_due = Meeting.objects.filter(datelte=soon, dategte=now, company__isnull=False)
    for meeting in meetings_due:
        company = meeting.company
        users = [task.assigned_to for task in company.tasks.filter(assigned_to__isnull=False).distinct()]
        for user in users:
            if not Notification.objects.filter(user=user, type='meeting_due_soon', related_object_id=meeting.id).exists():
                Notification.objects.create(
                    user=user,
                    type='meeting_due_soon',
                    title='Upcoming Meeting',
                    message=f"You have a meeting with {company.name} soon.",
                    related_object_id=meeting.id
                )