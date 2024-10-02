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
    path("admin/", admin.site.urls),
    # BookProductionService
    path(
        "book_production_service",
        views.get_book_production_services_list,
        name="book_production_services_list",
    ),
    path(
        "book_production_service/post",
        views.post_book_production_service,
        name="book_production_service_post",
    ),
    path(
        "book_production_service/<int:pk>",
        views.get_book_production_service,
        name="book_production_service",
    ),
    path(
        "book_production_service/<int:pk>/delete",
        views.delete_book_production_service,
        name="book_production_service_delete",
    ),
    path(
        "book_production_service/<int:pk>/put",
        views.put_book_production_service,
        name="book_production_service_put",
    ),
    path(
        "book_production_service/<int:pk>/add",
        views.post_service_to_project,
        name="book_production_service_add",
    ),
    path(
        "book_production_service/<int:pk>/add_image",
        views.post_book_production_service_image,
        name="book_production_service_add_image",
    ),
    # BookPublishingProject
    path(
        "book_publishing_project",
        views.get_book_publishing_projects,
        name="book_publishing_projects",
    ),
    path(
        "book_publishing_project/<int:pk>",
        views.get_book_publishing_project,
        name="book_publishing_project",
    ),
    path(
        "book_publishing_project/<int:pk>/put",
        views.put_book_publishing_project,
        name="book_publishing_project_put",
    ),
    path(
        "book_publishing_project/<int:pk>/form",
        views.form_book_publishing_project,
        name="book_publishing_project_form",
    ),
    path(
        "book_publishing_project/<int:pk>/resolve",
        views.resolve_book_publishing_project,
        name="book_publishing_project_resolve",
    ),
    path(
        "book_publishing_project/<int:pk>/delete",
        views.delete_book_publishing_project,
        name="book_publishing_project_delete",
    ),
    # SelectedServices
    path(
        "selected_services/<int:pk>/put",
        views.put_selected_service,
        name="selected_service_put",
    ),
    path(
        "selected_services/<int:pk>/delete",
        views.delete_selected_service,
        name="selected_service_delete",
    ),
    # User
    path("users/sign_up", views.sign_up_user, name="users_sign_up"),
    path("users/log_in", views.log_in_user, name="users_log_in"),
    path("users/log_out", views.log_out_user, name="users_log_out"),
    path("users/update", views.update_user, name="users_update"),
]

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.get_book_production_services_list_page, name='services'),
#     path('book_production_service/<int:id>/', views.get_book_production_service_page, name='service_url'),
#     path('book_publishing_project/<int:id>/', views.get_book_publishing_project_page, name='project'),
#     path('add_service_to_project/', views.add_book_production_service_to_project, name='add_service_to_project'),
#     path('delete_book_publishing_project/<int:id>/', views.delete_book_publishing_project, name='delete_book_publishing_project'),
# ]
