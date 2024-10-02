from rest_framework import serializers
from django.contrib.auth.models import User

from book_production.models import (
    BookProductionService,
    BookPublishingProject,
    SelectedServices,
)


# BookProductionService
class BookProductionServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookProductionService
        fields = ["pk", "title", "description", "is_active", "image_url", "price"]


# BookPublishingProject
class BookPublishingProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookPublishingProject
        fields = [
            "pk",
            "status",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "format",
            "circulation",
            "customer",
            "manager",
            "personal_discount",
        ]


class PutBookPublishingProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookPublishingProject
        fields = [
            "pk",
            "status",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "format",
            "circulation",
            "customer",
            "manager",
            "personal_discount",
        ]
        read_only_fields = [
            "pk",
            "status",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "customer",
            "manager",
            "personal_discount",
        ]


class ResolveBookPublishingProjectSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data.get("status", "") not in (
            BookPublishingProject.ProjectStatus.COMPLETED,
            BookPublishingProject.ProjectStatus.REJECTED,
        ):
            raise serializers.ValidationError("invalid status")
        return data

    class Meta:
        model = BookPublishingProject
        fields = [
            "pk",
            "status",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "format",
            "circulation",
            "customer",
            "manager",
            "personal_discount",
        ]
        read_only_fields = [
            "pk",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "format",
            "circulation",
            "customer",
            "manager",
            "personal_discount",
        ]


# SelectedServices
class SelectedServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectedServices
        fields = ["pk", "project", "service", "rate"]


class ServiceForProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookProductionService
        fields = ["pk", "title", "price", "image_url"]


class RelatedSerializer(serializers.ModelSerializer):
    service = ServiceForProjectSerializer()

    class Meta:
        model = SelectedServices
        fields = ["pk", "service", "rate"]


class FullBookPublishingProjectSerializer(serializers.ModelSerializer):
    services_list = RelatedSerializer(source="selectedservices_set", many=True)

    class Meta:
        model = BookPublishingProject
        fields = [
            "pk",
            "status",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "format",
            "circulation",
            "customer",
            "manager",
            "personal_discount",
            "services_list",
        ]


# User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()
        return instance
