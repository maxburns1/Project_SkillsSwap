from django.urls import path
from . import views

# This file maps URLs to view functions
# Example: /skills/ goes to skill_list view

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Skill URLs
    path('', views.skill_list, name='skill_list'),
    path('skill/<int:pk>/', views.skill_detail, name='skill_detail'),
    path('skill/create/', views.skill_create, name='skill_create'),
    path('skill/<int:pk>/edit/', views.skill_update, name='skill_update'),
    path('skill/<int:pk>/delete/', views.skill_delete, name='skill_delete'),
    
    # Review URLs
    path('skill/<int:skill_pk>/review/', views.review_create, name='review_create'),
    path('booking/<int:booking_pk>/learner-review/', views.learner_review_create, name='learner_review_create'),
    path('review/<int:review_pk>/delete/', views.review_delete, name='review_delete'),
    
    # Booking URLs
    path('skill/<int:skill_pk>/book/', views.booking_request_create, name='booking_create'),
    path('booking/<int:booking_pk>/respond/', views.booking_request_update, name='booking_update'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
