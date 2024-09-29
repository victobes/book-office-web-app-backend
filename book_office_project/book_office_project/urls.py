"""
URL configuration for book_office_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path

from book_production import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.get_book_production_services_list_page, name='services'),
    path('book_production_service/<int:id>/', views.get_book_production_service_page, name='service_url'),
    path('book_publishing_project/<int:id>/', views.get_book_publishing_project_page, name='project'),
    path('add_service_to_project/', views.add_book_production_service_to_project, name='add_service_to_project'),
    path('delete_book_publishing_project/<int:id>/', views.delete_book_publishing_project, name='delete_book_publishing_project'),
]
