from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import NotificationLog


# ==============================================================
# NOTIFICATIONS PAGE
# ==============================================================


@login_required
def notifications_page(request):

    notifications = (
        NotificationLog.objects
        .filter(
            recipient=request.user,
        )
        .select_related(
            "cad_model",
        )
        .order_by(
            "-created_at",
        )
    )

    return render(
        request,
        "exchange/notifications.html",
        {
            "notifications": notifications,
        },
    )