"""
URL configuration for Bilder_Resume project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from MainApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('vacancies/', views.VacancyListView.as_view(), name='vacancy_list'),
    path('vacancies/create/', views.VacancyCreateView.as_view(), name='vacancy_create'),
    path('vacancies/<int:pk>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
    path('resumes/', views.PublicResumeListView.as_view(), name='public_resume_list'),
    path('resumes/<int:pk>/', views.PublicResumeDetailView.as_view(), name='public_resume_detail'),
    path('', views.ResumeEditView.as_view(), name='home'),
    path('user-profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('resume/', views.ResumeView.as_view(), name='resume'),
    path('resume/edit/', views.ResumeEditView.as_view(), name='resume_edit'),
    
]
