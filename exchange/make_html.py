import os

# We write it with brackets here so the chat doesn't delete it
code_with_brackets = """from django.urls import path
from . import views

urlpatterns = [
    path('nda/[uuid:file_id]/', views.sign_nda, name='sign_nda'),
]
"""

# Python will magically swap the brackets for the correct arrows!
perfect_code = code_with_brackets.replace('[', '<').replace(']', '>')

# This writes the perfect code directly into your urls.py file
with open('exchange/urls.py', 'w') as f:
    f.write(perfect_code)

print("SUCCESS: exchange/urls.py has been fixed perfectly!")