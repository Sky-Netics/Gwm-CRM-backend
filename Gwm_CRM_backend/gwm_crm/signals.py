from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Task, Meeting
from .utils import create_notification

@receiver(post_save, sender=Task)
def handle_task_notifications(sender, instance, created, **kwargs):
    """
    Creates notifications for:
    - New task assignments
    - Due date reminders
    - Assignment changes
    """
    try:
        if created and instance.assigned_to:
            create_notification(
                user=instance.assigned_to,
                title=f"New Task: {instance.title}",
                message=f"You've been assigned: {instance.title}",
                notification_type='task_assigned',
                related_object_id=instance.id
            )
        
        elif (instance.due_date and 
              instance.assigned_to and
              instance.due_date <= timezone.now() + timezone.timedelta(hours=24)):
            create_notification(
                user=instance.assigned_to,
                title=f"Task Due Soon: {instance.title}",
                message=f"Due soon: {instance.title}",
                notification_type='task_due_soon',
                related_object_id=instance.id
            )

    except Exception as e:
        import logging
        logging.error(f"Task notification error: {str(e)}")

@receiver(post_save, sender=Meeting)
def handle_meeting_notifications(sender, instance, created, **kwargs):
    """
    Creates notifications for:
    - New meeting assignments
    - Upcoming meetings
    """
    try:
        if created and instance.assigned_to and instance.date:
            create_notification(
                user=instance.assigned_to,
                title="New Meeting Scheduled",
                message=f"Meeting on {instance.date.strftime('%b %d, %Y')}",
                notification_type='meeting_scheduled',
                related_object_id=instance.id
            )
            if instance.date <= timezone.now() + timezone.timedelta(hours=24):
                create_notification(
                    user=instance.assigned_to,
                    title="Meeting Reminder",
                    message=f"Meeting starting soon",
                    notification_type='meeting_reminder',
                    related_object_id=instance.id
                )
    except Exception as e:
        import logging
        logging.error(f"Meeting notification error: {str(e)}")