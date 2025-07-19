from django.db.models.signals import post_save, pre_save, m2m_changed
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

# @receiver(post_save, sender=Meeting)
# def handle_meeting_notifications(sender, instance, created, **kwargs):
#     """
#     Creates notifications for:
#     - New meeting assignments
#     - Upcoming meetings
#     """
#     try:
#         if created and instance.date:
#             for user in instance.users.all():
#                 create_notification(
#                     user=user,
#                     title="New Meeting Scheduled",
#                     message=f"Meeting on {instance.date.strftime('%b %d, %Y')}",
#                     notification_type='meeting_scheduled',
#                     related_object_id=instance.id
#                 )
                
#                 if instance.date <= timezone.now() + timezone.timedelta(hours=24):
#                     create_notification(
#                         user=user,
#                         title="Meeting Reminder",
#                         message="Meeting starting soon",
#                         notification_type='meeting_reminder',
#                         related_object_id=instance.id
#                     )
#     except Exception as e:
#         import logging
#         logging.error(f"Meeting notification error: {str(e)}")

@receiver(post_save, sender=Meeting)
def handle_new_meeting(sender, instance, created, **kwargs):
    """Handle initial meeting creation"""
    if created:
        for user in instance.users.all():
            _create_meeting_notifications(instance, user)

@receiver(m2m_changed, sender=Meeting.users.through)
def handle_meeting_attendees(sender, instance, action, pk_set, **kwargs):
    """Handle when users are added to meetings"""
    if action == "post_add":
        from django.contrib.auth import get_user_model
        User = get_user_model()
        for user_id in pk_set:
            user = User.objects.get(pk=user_id)
            _create_meeting_notifications(instance, user)

def _create_meeting_notifications(meeting, user):
    """Shared notification creation logic"""
    try:
        create_notification(
            user=user,
            title="New Meeting Scheduled",
            message=f"Meeting on {meeting.date.strftime('%b %d, %Y')}",
            notification_type='meeting_scheduled',
            related_object_id=meeting.id
        )
        
        if meeting.date <= timezone.now() + timezone.timedelta(hours=24):
            create_notification(
                user=user,
                title="Meeting Reminder",
                message=f"'{meeting.title}' starts soon",
                notification_type='meeting_reminder',
                related_object_id=meeting.id
            )
    except Exception as e:
        import logging
        logging.error(f"Meeting notification error for user {user.id}: {str(e)}")