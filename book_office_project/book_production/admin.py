from django.contrib import admin

# Register your models here.
from book_production.models import BookProductionService, BookPublishingProject, SelectedServices

admin.site.register(BookProductionService)
admin.site.register(BookPublishingProject)
admin.site.register(SelectedServices)