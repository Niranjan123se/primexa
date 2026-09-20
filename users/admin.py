from django.contrib import admin
from .models import ExpertProfile, LoginActivity, ServiceRequest, User

# This tells Django to show the User table in the admin panel
admin.site.register(User)


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "logged_in_at", "ip_address", "user_agent")
    list_filter = ("logged_in_at", "user__role")
    search_fields = ("user__username", "user__email", "ip_address")
    readonly_fields = ("user", "logged_in_at", "ip_address", "user_agent")
    date_hierarchy = "logged_in_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "city", "is_available", "is_verified")
    list_filter = ("is_available", "is_public_profile", "is_verified")
    search_fields = ("user__username", "user__email", "headline", "expertise")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("project_title", "request_type", "contact_name", "status", "created_at")
    list_filter = ("request_type", "status", "created_at")
    search_fields = ("project_title", "contact_name", "contact_email", "company_name")
    readonly_fields = ("submitted_by", "created_at")
