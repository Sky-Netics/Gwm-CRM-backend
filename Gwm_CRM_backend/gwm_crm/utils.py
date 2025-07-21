from django.utils import timezone
from .models import Notification
import logging

logger = logging.getLogger(__name__)

def create_notification(user, title, message, content_type , notification_type, related_object_id=None):
    try:
        notification = Notification.objects.create(
            user=user,
            title=title[:200], 
            message=message,
            content_type=content_type,
            type=notification_type,
            related_object_id=related_object_id,
            created_at=timezone.now()
        )
        logger.info(f"Created notification: {notification}")
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None