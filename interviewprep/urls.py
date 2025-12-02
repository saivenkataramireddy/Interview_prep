from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('add/', views.add_topic, name='add_topic'),
    path('toggle/<int:id>/', views.toggle_status, name='toggle_status'),
    path('delete/<int:id>/', views.delete_topic, name='delete_topic'),
    path('practice/', views.practice_view, name='practice'),  # 🔥 new
    path('progress/analytics/', views.progress_analytics_view, name='progress_analytics'),

]
    