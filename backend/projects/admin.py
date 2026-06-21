# backend/projects/admin.py

from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "user", "created_at"]
    search_fields = ["name", "user__username"]