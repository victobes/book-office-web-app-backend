from django.db import models
from django.contrib.auth.models import User


class BookProductionService(models.Model):
    title = models.CharField(max_length=130, unique=True, blank=False, null=False)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    image_url = models.CharField(max_length=255, null=True, blank="True", default="")
    price = models.CharField(max_length=50)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'book_production_services'


class BookPublishingProject(models.Model):
    class ProjectStatus(models.TextChoices):
        DRAFT = "DRAFT"
        DELETED = "DELETED"
        FORMED = "FORMED"
        COMPLETED = "COMPLETED"
        REJECTED = "REJECTED"

    class BookFormat(models.TextChoices):
        A_4 = "A4"
        A_5 = "A5"
        A_6 = "A6"
        SQUARE = "SQUARE"
        B_5 = "B5"
        
    status = models.CharField(
        max_length=10,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
    )

    creation_datetime = models.DateTimeField(auto_now_add=True)
    formation_datetime = models.DateTimeField(blank=True, null=True)
    completion_datetime = models.DateTimeField(blank=True, null=True)
    
    format = models.CharField(
        max_length=10,
        choices=BookFormat.choices,
        default=BookFormat.A_4,
    )
    
    circulation = models.IntegerField(blank=True, null=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_requests')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_requests', blank=True, null=True)
    personal_discount = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'book_publishing_projects'


class SelectedServices(models.Model):
    class Rate(models.TextChoices):
        BASE = "BASE"
        PREMIUM = "PREMIUM"
        PROFESSIONAL = "PROFESSIONAL"

    project = models.ForeignKey(BookPublishingProject, on_delete=models.CASCADE)
    service = models.ForeignKey(BookProductionService, on_delete=models.CASCADE)
    
    rate = models.CharField(
        max_length=20,
        choices=Rate.choices,
        default=Rate.BASE
    )

    def __str__(self):
        return f"{self.project_id}-{self.service_id}"

    class Meta:
        db_table = 'selected_services'
        unique_together = ('project', 'service'),