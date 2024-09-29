from datetime import datetime

from django.shortcuts import render, redirect
from django.db import connection
from django.db.models import Q

from book_production.models import (
    BookProductionService,
    BookPublishingProject,
    SelectedServices,
)

CUSTOMER_ID = 1


def get_publishing_project_data(project_id: int):
    """Формирует и возвращает данные проекта"""
    project = BookPublishingProject.objects.filter(
        ~Q(status=BookPublishingProject.ProjectStatus.DELETED), id=project_id
    ).first()

    if project is None:
        return {
            "id": project_id,
            "project_id": project_id,
            "circulation": 100,
            "format": BookPublishingProject.BookFormat.A_4,
            "selected_services_list": [],
        }

    selected_services = SelectedServices.objects.filter(
        project_id=project_id
    ).select_related("service")
    return {
        "id": project_id,
        "project_id": project_id,
        "circulation": project.circulation,
        "format": project.format,
        "selected_services_list": selected_services,
    }


def get_selected_services_count(project_id: int) -> int:
    """Возвращает количество выбранных услуг в проекте по его id"""
    return (
        SelectedServices.objects.filter(project_id=project_id)
        .select_related("service")
        .count()
    )


def get_book_production_services_list_page(request):
    """Возвращает страницу со списком услуг книжного издательства"""
    service_name = request.GET.get("book_production_service_name", "")
    project = BookPublishingProject.objects.filter(
        customer_id=CUSTOMER_ID, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    book_production_services_list = BookProductionService.objects.filter(
        title__istartswith=service_name, is_active=True
    )
    return render(
        request,
        "book_production_services_list.html",
        {
            "data": {
                "services": book_production_services_list,
                "selected_services_count": (
                    get_selected_services_count(project.id)
                    if project is not None
                    else 0
                ),
                "project_id": (project.id if project is not None else 0),
                "service_name": service_name,
            },
        },
    )


def get_book_production_service_page(request, id):
    """Возвращает страницу услуги книжного издательства"""
    data = BookProductionService.objects.filter(id=id).first()
    if data is None:
        return render(request, "book_production_service.html")
    return render(
        request,
        "book_production_service.html",
        {
            "data": {
                "service": data,
            }
        },
    )


def get_book_publishing_project_page(request, id: int):
    """Возвращает страницу проекта"""
    if BookPublishingProject.objects.filter(id=id, status=BookPublishingProject.ProjectStatus.DELETED).first() is not None:
        return redirect("services")
        
    return render(
        request,
        "book_publishing_project.html",
        {"data": get_publishing_project_data(id)},
    )


def add_service_to_project_request(project_id: int, service_id: int):
    """Добавляет услугу в проект"""
    selected_service = SelectedServices(project_id=project_id, service_id=service_id)
    selected_service.save()


def add_book_production_service_to_project(request):
    """Обрабатывает добавление услуги в проект"""
    if request.method != "POST":
        return redirect("services")
    data = request.POST
    service_id = data.get("add_to_project")
    if service_id is not None:
        project_id = get_or_create_customer_project(CUSTOMER_ID)
        add_service_to_project_request(project_id, service_id)
    return get_book_production_services_list_page(request)


def get_or_create_customer_project(customer_id: int) -> int:
    """
    Если у пользователя есть проект в статусе DRAFT, то возвращает его id.
    Если нет, то создает проект и возвращает его id.
    """
    draft_project = BookPublishingProject.objects.filter(
        customer_id=CUSTOMER_ID, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if draft_project is not None:
        return draft_project.id

    new_draft_project = BookPublishingProject(
        customer_id=CUSTOMER_ID,
        status=BookPublishingProject.ProjectStatus.DRAFT,
        circulation=100,
    )
    new_draft_project.save()
    return new_draft_project.id


def delete_project(project_id: int):
    """Удаляет проект по его id"""
    raw_query = "UPDATE book_publishing_projects SET status='DELETED' WHERE id=%s"
    with connection.cursor() as cursor:
        cursor.execute(raw_query, (project_id,))


def delete_book_publishing_project(request, id: int):
    """Обрабатывает удаление проекта"""
    if request.method != "POST":
        return redirect("project")

    data = request.POST
    action = data.get("request_action")
    if action == "delete_project":
        delete_project(id)
        return redirect("services")
    return get_book_publishing_project_page(request, id)
