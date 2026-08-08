from django.contrib import admin
from .models import User

# This tells Django to show the User table in the admin panel
admin.site.register(User)