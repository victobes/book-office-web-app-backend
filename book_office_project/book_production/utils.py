from book_production.serializers import *


def calculate_personal_discount(circulation):
    """Расчет персональной скидки"""
    if circulation > 100000:
        return 20
    if circulation > 50000:
        return 10
    return 0


def get_or_create_customer_project(user_id: int) -> int:
    """
    Если у пользователя есть проект в статусе DRAFT, то возвращает его id.
    Если нет, то создает проект и возвращает его id.
    """
    draft_project = BookPublishingProject.objects.filter(
        customer_id=user_id, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if draft_project is not None:
        return draft_project.id

    new_draft_project = BookPublishingProject(
        customer_id=user_id, status=BookPublishingProject.ProjectStatus.DRAFT
    )
    new_draft_project.save()
    return new_draft_project.id


def add_service_to_project_request(project_id: int, service_id: int):
    """Добавляет услугу в проект"""
    selected_service = SelectedServices(project_id=project_id, service_id=service_id)
    selected_service.save()
