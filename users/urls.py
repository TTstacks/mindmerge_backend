from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import LoginView, SignupView, UserView, SchoolView, UserUploadImageView



urlpatterns = [
    path('user/<int:pk>/', UserView.as_view()),
    path('user/', UserView.as_view()),
    path('user/image/', UserUploadImageView.as_view()),
    path('login', LoginView.as_view()),
    path('signup', SignupView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('school', SchoolView.as_view())
]
