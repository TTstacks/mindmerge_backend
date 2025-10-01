from django.urls import path, include
from projects.views import UserProjectview, TagListView, ProjectViewSet, ProjectSerachListView, BeamsAuthView, agora_webhook
from rest_framework import routers

router = routers.DefaultRouter()
router.register('project', ProjectViewSet, basename='project')


urlpatterns = [
    path('', include(router.urls)),
    path('user/<int:id>/projects/', UserProjectview.as_view()),
    path('user/projects/', UserProjectview.as_view()),
    path('user/beams-auth/', BeamsAuthView.as_view()),
    path('tags/', TagListView.as_view()),
    path('project-search/', ProjectSerachListView.as_view()),
    path('agora-webhook/', agora_webhook, name='agora-webhook')
]