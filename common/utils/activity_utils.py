from ..services.activity import ActivityLogService

def log_user_activity(user, action, obj=None, extra=None, request=None):
    ActivityLogService.log(user, action, obj=obj, extra=extra, request=request)