from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import LoginActivity


def get_client_ip(request):
    """Return the client address without trusting spoofable proxy headers by default."""
    if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def record_successful_login(sender, request, user, **kwargs):
    LoginActivity.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
    )
