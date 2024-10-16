import os
import uuid

from datetime import datetime
from dateutil.parser import parse
from django.db.models import Q
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    parser_classes,
)
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.parsers import FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from book_office_project import settings
from book_production.minio import MinioStorage
from book_production.serializers import *
from book_production.authorization import (
    AuthBySessionID,
    AuthBySessionIDIfExists,
    IsAuth,
    IsManagerAuth,
)
from book_production.redis import session_storage
from book_production.utils import *


# BookProductionService
@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "book_production_service_name",
            type=openapi.TYPE_STRING,
            description="book_production_service_name",
            in_=openapi.IN_QUERY,
        ),
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "book_production_services": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                ),
                "book_publishing_project_id": openapi.Schema(type=openapi.TYPE_NUMBER),
                "selected_services_count": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([AuthBySessionIDIfExists])
def get_book_production_services_list(request):
    """
    Получение списка услуг книжного издательства
    """
    user = request.user
    service_name = request.query_params.get("book_production_service_name", "")
    services_list = BookProductionService.objects.filter(
        title__istartswith=service_name, is_active=True
    )

    serializer = BookProductionServiceSerializer(services_list, many=True)

    project = None
    selected_services_count = 0

    if user is not None:
        project = BookPublishingProject.objects.filter(
            customer_id=user.pk, status=BookPublishingProject.ProjectStatus.DRAFT
        ).first()

        if project is not None:
            selected_services_count = SelectedServices.objects.filter(
                project_id=project.id
            ).count()

    return Response(
        {
            "book_production_services": serializer.data,
            "book_publishing_project_id": project.id if project else None,
            "selected_services_count": selected_services_count,
        },
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="post",
    request_body=BookProductionServiceSerializer,
    responses={
        status.HTTP_200_OK: BookProductionServiceSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["POST"])
@permission_classes([IsManagerAuth])
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


@swagger_auto_schema(
    method="post",
    manual_parameters=[
        openapi.Parameter(
            name="image",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_FILE,
            required=True,
            description="Image",
        )
    ],
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["POST"])
@permission_classes([IsManagerAuth])
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


@swagger_auto_schema(
    method="get",
    responses={
        status.HTTP_200_OK: BookProductionServiceSerializer(),
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_book_production_service(request, pk):
    """
    Получение услуги книжного издательства
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)
    serialized_service = BookProductionServiceSerializer(service)
    return Response(serialized_service.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="delete",
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["DELETE"])
@permission_classes([IsManagerAuth])
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


@swagger_auto_schema(
    method="put",
    request_body=BookProductionServiceSerializer,
    responses={
        status.HTTP_200_OK: BookProductionServiceSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsManagerAuth])
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


@swagger_auto_schema(
    method="post",
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["POST"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def post_service_to_project(request, pk):
    """
    Добавление услуги книжного издательства в проект
    """
    service = BookProductionService.objects.filter(id=pk, is_active=True).first()
    if service is None:
        return Response("Service not found", status=status.HTTP_404_NOT_FOUND)
    project_id = get_or_create_customer_project(request.user.id)
    add_service_to_project_request(project_id, pk)
    return Response(status=status.HTTP_200_OK)


# BookPublishingProject


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "status",
            type=openapi.TYPE_STRING,
            description="status",
            in_=openapi.IN_QUERY,
        ),
        openapi.Parameter(
            "formation_start",
            type=openapi.TYPE_STRING,
            description="status",
            in_=openapi.IN_QUERY,
            format=openapi.FORMAT_DATETIME,
        ),
        openapi.Parameter(
            "formation_end",
            type=openapi.TYPE_STRING,
            description="status",
            in_=openapi.IN_QUERY,
            format=openapi.FORMAT_DATETIME,
        ),
    ],
    responses={
        status.HTTP_200_OK: BookPublishingProjectSerializer(many=True),
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["GET"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
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

    if not request.user.is_staff:
        filters &= Q(customer=request.user)

    projects = BookPublishingProject.objects.filter(filters)
    serializer = BookPublishingProjectSerializer(projects, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    responses={
        status.HTTP_200_OK: FullBookPublishingProjectSerializer(),
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["GET"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def get_book_publishing_project(request, pk):
    """
    Получение издательского проекта
    """
    filters = Q(id=pk) & ~Q(status=BookPublishingProject.ProjectStatus.DELETED)
    project = BookPublishingProject.objects.filter(filters).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and project.customer != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = FullBookPublishingProjectSerializer(project)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="put",
    request_body=PutBookPublishingProjectSerializer,
    responses={
        status.HTTP_200_OK: PutBookPublishingProjectSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def put_book_publishing_project(request, pk):
    """
    Изменение издательского проекта
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and project.customer != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = PutBookPublishingProjectSerializer(
        project, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="put",
    responses={
        status.HTTP_200_OK: BookPublishingProjectSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def form_book_publishing_project(request, pk):
    """
    Формирование издательского проекта
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and project.customer != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

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


@swagger_auto_schema(
    method="put",
    responses={
        status.HTTP_200_OK: ResolveBookPublishingProjectSerializer(),
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsManagerAuth])
@authentication_classes([AuthBySessionID])
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
    project.manager = request.user
    project.save()

    serializer = BookPublishingProjectSerializer(project)
    return Response(serializer.data)


@swagger_auto_schema(
    method="delete",
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_book_publishing_project(request, pk):
    """
    Удаление издательского проекта
    """
    project = BookPublishingProject.objects.filter(
        id=pk, status=BookPublishingProject.ProjectStatus.DRAFT
    ).first()
    if project is None:
        return Response("Project not found", status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_staff and project.customer != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    project.status = BookPublishingProject.RequestStatus.DELETED
    project.save()
    return Response(status=status.HTTP_200_OK)


# SelectedServices


@swagger_auto_schema(
    method="put",
    request_body=SelectedServicesSerializer,
    responses={
        status.HTTP_200_OK: SelectedServicesSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def put_selected_service(request, project_pk, service_pk):
    """
    Изменение данных о выбранной услуге в проекте
    """
    project = BookPublishingProject.objects.filter(id=project_pk).first()
    if project is None:
        return Response(
            "BookPublishingProject not found", status=status.HTTP_404_NOT_FOUND
        )
    if not request.user.is_staff and project.customer != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

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


@swagger_auto_schema(
    method="delete",
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_selected_service(request, project_pk, service_pk):
    """
    Удаление выбранной услуги из проекта
    """
    project = BookPublishingProject.objects.filter(id=project_pk).first()
    if project is None:
        return Response(
            "BookPublishingProject not found", status=status.HTTP_404_NOT_FOUND
        )
    if not request.user.is_staff and project.customer != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    selected_service = SelectedServices.objects.filter(
        project_id=project_pk, service_id=service_pk
    ).first()
    if selected_service is None:
        return Response("Selected service not found", status=status.HTTP_404_NOT_FOUND)
    selected_service.delete()
    return Response(status=status.HTTP_200_OK)


# User


@swagger_auto_schema(
    method="post",
    request_body=UserSerializer,
    responses={
        status.HTTP_201_CREATED: "Created",
        status.HTTP_400_BAD_REQUEST: "Bad Request",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_up_user(request):
    """
    Создание пользователя
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    manual_parameters=[
        openapi.Parameter(
            "username",
            type=openapi.TYPE_STRING,
            description="username",
            in_=openapi.IN_FORM,
            required=True,
        ),
        openapi.Parameter(
            "password",
            type=openapi.TYPE_STRING,
            description="password",
            in_=openapi.IN_FORM,
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_400_BAD_REQUEST: "Bad Request",
    },
)
@api_view(["POST"])
@parser_classes((FormParser,))
@permission_classes([AllowAny])
def log_in_user(request):
    """
    Вход
    """
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(username=username, password=password)
    if user is not None:
        session_id = str(uuid.uuid4())
        session_storage.set(session_id, username)
        response = Response(status=status.HTTP_200_OK)
        response.set_cookie("session_id", session_id, samesite="lax")
        return response
    return Response(
        {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="post",
    responses={
        status.HTTP_204_NO_CONTENT: "No content",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["POST"])
@permission_classes([IsAuth])
def log_out_user(request):
    """
    Выход
    """
    session_id = request.COOKIES["session_id"]
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(
    method="put",
    request_body=UserSerializer,
    responses={
        status.HTTP_200_OK: UserSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_user(request):
    """
    Обновление данных пользователя
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
