from django.urls import path
from .models import User
from .views import RegisterUserView, ListUserView, UserDetailView


urlpatterns=[
    path('register/', RegisterUserView.as_view(), name='user-register'),
    path('user/', ListUserView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]