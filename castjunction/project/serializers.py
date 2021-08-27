"""Serializers for jobs and groups."""
import json

from django.contrib.contenttypes.models import ContentType
from drf_extra_fields.fields import IntegerRangeField, FloatRangeField, DateRangeField

from rest_framework import serializers

from pinax.likes.models import Like
from cities.models import City

from multimedia.serializers import ImageSerializer
from utils import choices
from utils.utils import ChoicesField
from application.models import State

# from .search_indexes import JobIndex
from .models import Job, Group, Key


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields`.

    Argument that controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        """Don't pass the 'fields' arg up to the superclass."""
        exclude_fields = kwargs.pop("exclude_fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if exclude_fields is not None:
            # Drop any fields that are specified in the `fields` argument.
            exclude = set(exclude_fields)
            for field_name in exclude:
                self.fields.pop(field_name)


class RequiredInformationSerializerFiled(serializers.Field):
    def to_representation(self, data):
        information = {}
        for info in data:
            information[info] = json.loads(data[info])
        return [information]


class GroupSerializer(serializers.Field):
    """Custom group serailzer for job creation."""

    def to_representation(self, data):
        return {
            "id": data.id,
            "title": data.title,
            "description": data.description,
            "start_date": data.start_date,
        }

    def to_internal_value(self, id):
        try:
            group = Group.objects.get(id=id)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Group doesn not exist")
        return group


class JobSerializer(DynamicFieldsModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    application = serializers.SerializerMethodField()
    location = serializers.SlugRelatedField(
        slug_field="name_std",
        queryset=City.objects.only("id", "name", "name_std").all(),
    )
    required_gender = ChoicesField(choices=choices.GENDER_CHOICES)
    likes = serializers.SerializerMethodField(read_only=True)
    required_information_to_apply = RequiredInformationSerializerFiled(read_only=True)
    reason_for_rejection = serializers.SerializerMethodField()
    group = GroupSerializer(required=False)
    images = ImageSerializer(many=True, read_only=True)
    status = ChoicesField(
        choices=choices.JOB_STATE_CHOICES, default=choices.PENDING_APPROVAL
    )
    job_type = ChoicesField(choices=choices.JOB_TYPE_CHOICES, default=choices.OTHER)
    submission_deadline = serializers.DateField(read_only=True)
    ages = IntegerRangeField()
    heights = FloatRangeField()
    budgets = IntegerRangeField()
    audition_range = DateRangeField()

    class Meta:
        model = Job
        fields = (
            "id",
            "created_at",
            "created_by",
            "role_position",
            "title",
            "description",
            "ages",
            "required_gender",
            "location",
            "required_information_to_apply",
            "required_tokens",
            "status",
            "reason_for_rejection",
            "application",
            "submission_deadline",
            "group",
            "likes",
            "images",
            "number_of_vacancies",
            "featured",
            "skin_type",
            "hair_type",
            "eye_color",
            "body_type",
            "audition_range",
            "language",
            "heights",
            "budgets",
            "job_type",
        )

    def create(self, validated_data):
        return Job.objects.create(**validated_data)

    def get_required_gender(self, obj):
        return obj.get_required_gender_display()

    def get_job_type(self, obj):
        return obj.get_job_type_display()

    def get_application(self, obj):
        try:
            if "request" in self.context:
                request = self.context["request"]
                user = request.user
                from application.serializers import ApplicationSerializer

                return ApplicationSerializer(
                    obj.applications.get(user=user),
                    context={"request": self.context["request"]},
                ).data
        except:
            pass
        return None

    def get_reason_for_rejection(self, obj):
        if obj.status == choices.REMOVED:
            return obj.reason_for_rejection
        else:
            return None

    def get_likes(self, obj):
        try:
            if "request" in self.context:
                user = self.context["request"].user
                like = Like.objects.filter(
                    sender=user,
                    receiver_content_type=ContentType.objects.get_for_model(Job),
                    receiver_object_id=obj.id,
                )
                if like:
                    return True
        except:
            pass
        return False


class JobShortSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Job
        fields = ("id", "role_position", "title", "description", "audition_range")


class JobDetailSerializer(JobSerializer):
    count = serializers.SerializerMethodField()
    applicants = serializers.SerializerMethodField()

    class Meta:
        model = Job
        exclude = ("application",)

    def get_count(self, obj):
        count = {}
        count["applied"] = obj.applications.filter(state=State.APPLIED).count()
        count["invited"] = obj.applications.filter(state=State.INVITED).count()
        count["shortlisted"] = obj.applications.filter(state=State.SHORTLISTED).count()
        return count

    def get_applicants(self, obj):
        applicants = obj.applicants.exclude(
            application__state=State.IGNORED
        ).values_list("id", flat=True)
        return applicants


class KeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Key
        fields = (
            "key_name",
            "title",
            "title_director_display",
            "key_type",
            "description",
        )
