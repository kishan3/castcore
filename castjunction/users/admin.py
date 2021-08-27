"""Admin panel for users."""
from __future__ import absolute_import, unicode_literals

from django import forms

from django.contrib import admin
from .models import (
    User,
    Person,
    Company,
    PersonType,
    Bio,
    Skill,
    Education,
    Institute,
    Language,
    Experience,
    SearchableField,
    UserIncentives,
)
from project.admin import ImageInline


class PersonAdminForm(forms.ModelForm):
    def clean(self):
        if not self.data.get("phone") and not self.data.get("email"):
            raise forms.ValidationError("Email and Phone both can not be null.")
        super().clean()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "phone",
    )
    # define the raw_id_fields
    raw_id_fields = ("city",)
    # define the autocomplete_lookup_fields
    autocomplete_lookup_fields = {
        "fk": ["city"],
    }


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "phone",
        "date_joined",
        "get_typs",
        "gender",
        "image_count",
    )
    raw_id_fields = ("city", "nationality")
    list_filter = (
        "date_joined",
        "gender",
    )
    search_fields = ("email", "first_name", "last_name", "phone")
    # define the autocomplete_lookup_fields
    autocomplete_lookup_fields = {
        "fk": ["city", "nationality"],
    }
    inlines = [
        ImageInline,
    ]

    def image_count(self, obj):
        return obj.images.count()

    def get_typs(self, obj):
        return ",".join(p.person_type for p in obj.typ.all())


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone",
    )
    inlines = [
        ImageInline,
    ]


@admin.register(PersonType)
class PersonTypeAdmin(admin.ModelAdmin):
    list_display = ("person_type",)


@admin.register(Bio)
class BioAdmin(admin.ModelAdmin):
    list_display = ("id", "person", "data")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("skill_name",)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "institute",
        "start_date",
        "end_date",
        "degree",
        "grade",
        "field_of_study",
        "social_activites",
        "description",
    )


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    # define the raw_id_fields
    raw_id_fields = ("location",)
    # define the autocomplete_lookup_fields
    autocomplete_lookup_fields = {
        "fk": ["location"],
    }
    list_display = (
        "id",
        "institute_name",
        "established_year",
        "location",
    )


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("language_name",)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    # define the raw_id_fields
    raw_id_fields = ("location",)
    # define the autocomplete_lookup_fields
    autocomplete_lookup_fields = {
        "fk": ["location"],
    }
    list_display = (
        "production_house",
        "title",
        "role",
        "person",
    )


@admin.register(SearchableField)
class SearchableFieldAdmin(admin.ModelAdmin):
    list_display = ("model_name", "field_name", "value", "data")


@admin.register(UserIncentives)
class UserIncentivesAdmin(admin.ModelAdmin):
    pass
