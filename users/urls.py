
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('register/oem/', views.register_oem, name='register_oem'),
    path('register/vendor/', views.register_vendor, name='register_vendor'),

    path(
        'terms-conditions/',
        views.terms_conditions,
        name='terms_conditions'
    ),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='users/login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        views.logout_user,
        name='logout'
    ),
]
