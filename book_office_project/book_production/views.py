import os

from datetime import datetime
from dateutil.parser import parse
from django.db.models import Q
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from book_office_project import settings
from book_production.minio import MinioStorage
from book_production.serializers import *

SINGLETON_USER = User(id=1, username="admin")
SINGLETON_MANAGER = User(id=2, username="manager")

# BookProductionService


@api_view(["GET"])
def get_book_production_services_list(request):
    """
    Получение списка услуг книжного издательства
    """
    service_name = request.query_params.get("book_production_service_name", "")
    project = BookPublishingProject.objects.filter(
        customer_id=SINGLETON_USER.id, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    services_list = BookProductionService.objects.filter(
        title__istartswith=service_name, is_active=True
    )

    serializer = BookProductionServiceSerializer(services_list, many=True)

    project_id = None
    selected_services_count = 0
    if project:
        project_id = project.id
        selected_services_count = get_selected_services_count(project.id)

    return Response(
        {
            "services": serializer.data,
            "project_id": project_id,
            "selected_services_count": selected_services_count,
        },
        status=status.HTTP_200_OK,
    )


def get_selected_services_count(project_id: int) -> int:
    """Возвращает количество выбранных услуг в проекте по его id"""
    return (
        SelectedServices.objects.filter(project_id=project_id)
        .select_related("service")
        .count()
    )


@api_view(["POST"])
def post_book_production_service(request):
    """
    Добавление услуги книжного издательства
    """
    serializer = BookProductionServiceSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    new_service = serializer.save()
    serializer = BookProductionServiceSerializer(new_service)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def post_book_production_service_image(request, pk):
    """
    Загрузка изображения услуги книжного издательства в Minio
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)

    minio_storage = MinioStorage(
        endpoint=settings.MINIO_ENDPOINT_URL,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )

    file = request.FILES.get("image")
    if not file:
        return Response("No image in request", status=status.HTTP_400_BAD_REQUEST)

    file_extension = os.path.splitext(file.name)[1]
    file_name = f"{pk}{file_extension}"

    try:
        minio_storage.load_file(settings.MINIO_BUCKET_NAME, file_name, file)
    except Exception as e:
        return Response(
            f"Failed to load image: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    service.image_url = (
        f"http://{settings.MINIO_ENDPOINT_URL}/{settings.MINIO_BUCKET_NAME}/{file_name}"
    )
    service.save()
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
def get_book_production_service(request, pk):
    """
    Получение услуги книжного издательства
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)
    serialized_service = BookProductionServiceSerializer(service)
    return Response(serialized_service.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_book_production_service(request, pk):
    """
    Удаление услуги книжного издательства
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)

    if service.image_url != "":
        minio_storage = MinioStorage(
            endpoint=settings.MINIO_ENDPOINT_URL,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        file_extension = os.path.splitext(service.image_url)[1]
        file_name = f"{pk}{file_extension}"
        try:
            minio_storage.delete_file(settings.MINIO_BUCKET_NAME, file_name)
        except Exception as e:
            return Response(
                f"Failed to delete image: {e}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        service.image_url = ""

    service.is_active = False
    service.save()
    return Response(status=status.HTTP_200_OK)


@api_view(["PUT"])
def put_book_production_service(request, pk):
    """
    Изменение услуги книжного издательства
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)

    serializer = BookProductionServiceSerializer(
        service, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def post_service_to_project(request, pk):
    """
    Добавление услуги книжного издательства в проект
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)
    project_id = get_or_create_customer_project(SINGLETON_USER.id)
    add_service_to_project_request(project_id, pk)
    return Response(status=status.HTTP_200_OK)


def get_or_create_customer_project(customer_id: int) -> int:
    """
    Если у пользователя есть проект в статусе DRAFT, то возвращает его id.
    Если нет, то создает проект и возвращает его id.
    """
    draft_project = BookPublishingProject.objects.filter(
        customer_id=SINGLETON_USER.id, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if draft_project is not None:
        return draft_project.id

    new_draft_project = BookPublishingProject(
        customer_id=SINGLETON_USER.id, status=BookPublishingProject.ProjectStatus.DRAFT
    )
    new_draft_project.save()
    return new_draft_project.id


def add_service_to_project_request(project_id: int, service_id: int):
    """Добавляет услугу в проект"""
    selected_service = SelectedServices(project_id=project_id, service_id=service_id)
    selected_service.save()


# BookPublishingProject


@api_view(["GET"])
def get_book_publishing_projects(request):
    """
    Получение списка издательских проектов
    """
    status_filter = request.query_params.get("status")
    formation_datetime_start_filter = request.query_params.get("formation_start")
    formation_datetime_end_filter = request.query_params.get("formation_end")

    filters = ~Q(status=BookPublishingProject.ProjectStatus.DELETED)
    if status_filter is not None:
        filters &= Q(status=status_filter.upper())
    if formation_datetime_start_filter is not None:
        filters &= Q(formation_datetime__gte=parse(formation_datetime_start_filter))
    if formation_datetime_end_filter is not None:
        filters &= Q(formation_datetime__lte=parse(formation_datetime_end_filter))

    projects = BookPublishingProject.objects.filter(filters)
    serializer = BookPublishingProjectSerializer(projects, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_book_publishing_project(request, pk):
    """
    Получение издательского проекта
    """
    filters = Q(id=pk) & ~Q(status=BookPublishingProject.ProjectStatus.DELETED)
    project = BookPublishingProject.objects.filter(filters).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    serializer = FullBookPublishingProjectSerializer(project)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def put_book_publishing_project(request, pk):
    """
    Изменение издательского проекта
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    serializer = PutBookPublishingProjectSerializer(
        project, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def form_book_publishing_project(request, pk):
    """
    Формирование издательского проекта
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    if (
        project.circulation is None
        or project.circulation == ""
        or project.circulation < 100
    ):
        return Response(
            "Circulation is empty or too small", status=status.HTTP_400_BAD_REQUEST
        )

    project.status = BookPublishingProject.ProjectStatus.FORMED
    project.formation_datetime = datetime.now()
    project.save()
    serializer = BookPublishingProjectSerializer(project)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def resolve_book_publishing_project(request, pk):
    """
    Закрытие издательского проекта модератором
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.FORMED
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    serializer = ResolveBookPublishingProjectSerializer(
        project, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    project = BookPublishingProject.objects.get(id=pk)
    project.completion_datetime = datetime.now()
    project.personal_discount = caculate_personal_discount(project.circulation)
    project.SINGLETON_MANAGER = SINGLETON_MANAGER
    project.save()

    serializer = BookPublishingProjectSerializer(project)
    return Response(serializer.data)


def caculate_personal_discount(circulation):
    """Расчет персональной скидки"""
    if circulation > 100000:
        return 20
    if circulation > 50000:
        return 10
    return 0


@api_view(["DELETE"])
def delete_book_publishing_project(request, pk):
    """
    Удаление издательского проекта
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    project.status = BookPublishingProject.RequestStatus.DELETED
    project.save()
    return Response(status=status.HTTP_200_OK)


# SelectedServices


@api_view(["PUT"])
def put_selected_service(request, project_pk, service_pk):
    """
    Изменение данных о выбранной услуге в проекте
    """
    selected_service = SelectedServices.objects.filter(
        project_id=project_pk, service_id=service_pk
    ).first()
    if selected_service is None:
        return Response("Selected service not found", status=status.HTTP_404_NOT_FOUND)
    serializer = SelectedServicesSerializer(
        selected_service, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_selected_service(request, project_pk, service_pk):
    """
    Удаление выбранной услуги из проекта
    """
    selected_service = SelectedServices.objects.filter(
        project_id=project_pk, service_id=service_pk
    ).first()
    if selected_service is None:
        return Response("Selected service not found", status=status.HTTP_404_NOT_FOUND)
    selected_service.delete()
    return Response(status=status.HTTP_200_OK)


# User


@api_view(["POST"])
def sign_up_user(request):
    """
    Создание пользователя
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def log_in_user(request):
    """
    Вход
    """
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(username=username, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)
    return Response(
        {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def log_out_user(request):
    """
    Выход
    """
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user(request):
    """
    Обновление данных пользователя
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# def get_publishing_project_data(project_id: int):
#     """Формирует и возвращает данные проекта"""
#     project = BookPublishingProject.objects.filter(
#         ~Q(status=BookPublishingProject.ProjectStatus.DELETED), id=project_id
#     ).first()

#     if project is None:
#         return {
#             "id": project_id,
#             "project_id": project_id,
#             "circulation": 100,
#             "format": BookPublishingProject.BookFormat.A_4,
#             "selected_services_list": [],
#         }

#     selected_services = SelectedServices.objects.filter(
#         project_id=project_id
#     ).select_related("service")
#     return {
#         "id": project_id,
#         "project_id": project_id,
#         "circulation": project.circulation,
#         "format": project.format,
#         "selected_services_list": selected_services,
#     }


# def get_selected_services_count(project_id: int) -> int:
#     """Возвращает количество выбранных услуг в проекте по его id"""
#     return (
#         SelectedServices.objects.filter(project_id=project_id)
#         .select_related("service")
#         .count()
#     )


# def get_book_production_services_list_page(request):
#     """Возвращает страницу со списком услуг книжного издательства"""
#     service_name = request.GET.get("book_production_service_name", "")
#     project = BookPublishingProject.objects.filter(
#         customer_id=CUSTOMER_ID, status=BookPublishingProject.ProjectStatus.DRAFT
#     ).first()
#     book_production_services_list = BookProductionService.objects.filter(
#         title__istartswith=service_name, is_active=True
#     )
#     return render(
#         request,
#         "book_production_services_list.html",
#         {
#             "data": {
#                 "services": book_production_services_list,
#                 "selected_services_count": (
#                     get_selected_services_count(project.id)
#                     if project is not None
#                     else 0
#                 ),
#                 "project_id": (project.id if project is not None else 0),
#                 "service_name": service_name,
#             },
#         },
#     )


# def get_book_production_service_page(request, id):
#     """Возвращает страницу услуги книжного издательства"""
#     data = BookProductionService.objects.filter(id=id).first()
#     if data is None:
#         return render(request, "book_production_service.html")
#     return render(
#         request,
#         "book_production_service.html",
#         {
#             "data": {
#                 "service": data,
#             }
#         },
#     )


# def get_book_publishing_project_page(request, id: int):
#     """Возвращает страницу проекта"""
#     if BookPublishingProject.objects.filter(id=id, status=BookPublishingProject.ProjectStatus.DELETED).first() is not None:
#         return redirect("services")

#     return render(
#         request,
#         "book_publishing_project.html",
#         {"data": get_publishing_project_data(id)},
#     )


# def add_service_to_project_request(project_id: int, service_id: int):
#     """Добавляет услугу в проект"""
#     selected_service = SelectedServices(project_id=project_id, service_id=service_id)
#     selected_service.save()


# def add_book_production_service_to_project(request):
#     """Обрабатывает добавление услуги в проект"""
#     if request.method != "POST":
#         return redirect("services")
#     data = request.POST
#     service_id = data.get("add_to_project")
#     if service_id is not None:
#         project_id = get_or_create_customer_project(CUSTOMER_ID)
#         add_service_to_project_request(project_id, service_id)
#     return get_book_production_services_list_page(request)


# def get_or_create_customer_project(customer_id: int) -> int:
#     """
#     Если у пользователя есть проект в статусе DRAFT, то возвращает его id.
#     Если нет, то создает проект и возвращает его id.
#     """
#     draft_project = BookPublishingProject.objects.filter(
#         customer_id=CUSTOMER_ID, status=BookPublishingProject.ProjectStatus.DRAFT
#     ).first()
#     if draft_project is not None:
#         return draft_project.id

#     new_draft_project = BookPublishingProject(
#         customer_id=CUSTOMER_ID,
#         status=BookPublishingProject.ProjectStatus.DRAFT,
#         circulation=100,
#     )
#     new_draft_project.save()
#     return new_draft_project.id


# def delete_project(project_id: int):
#     """Удаляет проект по его id"""
#     raw_query = "UPDATE book_publishing_projects SET status='DELETED' WHERE id=%s"
#     with connection.cursor() as cursor:
#         cursor.execute(raw_query, (project_id,))


# def delete_book_publishing_project(request, id: int):
#     """Обрабатывает удаление проекта"""
#     if request.method != "POST":
#         return redirect("project")

#     data = request.POST
#     action = data.get("request_action")
#     if action == "delete_project":
#         delete_project(id)
#         return redirect("services")
#     return get_book_publishing_project_page(request, id)
