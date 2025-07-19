from django.utils import timezone
from .models import Notification

def create_notification(user, title, message, notification_type, related_object_id=None):
    """Utility function to create notifications"""
    try:
        return Notification.objects.create(
            user=user,
            title=title[:200],  # Ensure it fits in CharField
            message=message,
            type=notification_type,
            related_object_id=related_object_id,
            created_at=timezone.now()
        )
    except Exception as e:
        import logging
        logging.error(f"Notification creation failed: {str(e)}")
        return None