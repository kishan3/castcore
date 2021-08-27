"""Views for application app."""

import django_fsm
from django_fsm import has_transition_perm

from rest_framework import viewsets, mixins, status, generics, filters
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from project.models import Job
from project.permissions import IsJobOwner
from user_tokens.accounts_manager import debit_tokens_from_user
from users.permissions import IsCastingDirector
from users.models import User
from utils.utils import check_person_information
from utils import choices

from .serializers import ApplicationSerializer, MobileAppVersionSerializer
from .models import Application, State, MobileAppVersion
from .utils import checks_before_apply


class ApplicationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Create, Retrieve, List applications."""

    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filter_fields = ("state",)
    ordering_fields = ("updated_at",)
    ordering = ("-updated_at",)

    def get_queryset(self):
        """Return all applications for this job id."""
        return Application.objects.filter(job__id=self.kwargs["job_id"])

    def get_permissions(self):
        if self.request.method == "GET":
            return (IsJobOwner(),)
        return (IsAuthenticated(),)

    def __init__(self, **kwargs):
        """Init method."""
        self._data = {}
        super().__init__(**kwargs)

    def create(self, request, job_id=None, **kwargs):
        """Create application."""
        user = request.user
        if job_id:
            try:
                job = Job.objects.get(pk=job_id)
            except Job.DoesNotExist:
                raise NotFound("Job with job id {} does not exist.".format(job_id))
        else:
            raise ValidationError("Job id is required to apply for a job.")
        action = request.data.get("action")

        if not action:
            raise ValidationError("Valid action key is required to create application.")
        elif action == State.APPLIED:
            checks_before_apply(user, job)
            # keys = job.required_information_to_apply.keys()
            # for model_name in keys:
            #     data_dict = json.loads(job.required_information_to_apply[model_name])
            #     if model_name in ['Image', 'Video', 'Audio']:
            #         model = apps.get_model(app_label='multimedia', model_name=model_name)
            #         try:
            #             required = int(data_dict['required_value'][0])
            #         except ValueError as e:
            #             raise e
            #         if model.objects.filter(object_id=user.id).count() < required:
            #             raise ValidationError("Please upload atleast {} {} to apply.".format(required, model_name))
            #     elif model_name in ['Bio', 'Experience']:
            #         model = apps.get_model(app_label='users', model_name=model_name)
            #         try:
            #             model_object = model.objects.get(person=user)
            #         except model.DoesNotExist:
            #             raise NotFound("{0} for user not found".format(model_name))
            #         for data in data_dict:
            #             # in case key name is given big.
            #             field = data['key_name'].lower()
            #             try:
            #                 value = getattr(model_object, field)
            #             except AttributeError:
            #                 raise ValidationError("{0} has no attribute {1}".format(model_object, field))

            #             required = data['required_value']
            #             comparator = data['comparator']
            #             if comparator != "range":
            #                 try:
            #                     required = float(required[0])
            #                 except ValueError:
            #                     required = int(required[0])
            #                 compare_function = getattr(operator, comparator)
            #                 if not compare_function(value, required):
            #                     raise ValidationError("{0} for {1} is not as required {2}".format(value, field, required))
            #             elif comparator == "range":
            #                 try:
            #                     start = int(required[0])
            #                     end = int(required[1])
            #                 except ValueError:
            #                     start = float(required[0])
            #                     end = float(required[1])

            #                 v_range = range(start, end+1)
            #                 if value not in v_range:
            #                     raise ValidationError("{0} for {1} is not in range required {2}".format(value, field, v_range))

            # Everything is fine user can apply if has not applied before.
            application, created = Application.objects.get_or_create(user=user, job=job)
            # serializer = self.serializer_class(application)

            if created or application.state in [State.PIPELINED, State.IGNORED]:
                debit_tokens_from_user(user, job.required_tokens)
                application.applied()
                application.save()

        elif action in [State.PIPELINED, State.IGNORED]:
            application, created = Application.objects.get_or_create(
                user=user, job=job, state=action
            )
        else:
            raise ValidationError(
                "Valid actions are '%s' '%s' or '%s'."
                % (State.APPLIED, State.PIPELINED, State.IGNORED)
            )
        if created:
            status_i = status.HTTP_201_CREATED
        else:
            status_i = status.HTTP_200_OK
        serializer = self.serializer_class(
            application, context={"request": self.request}
        )
        return Response(serializer.data, status=status_i)

    def update(self, request, *args, **kwargs):
        """Update application state and add audition invite information."""
        if request.data.get("state"):
            state = request.data.get("state")
            instance = self.get_object()
            try:
                change_of_state = getattr(Application, state)
            except AttributeError:
                raise ValidationError("Application state can not be {}".format(state))

            if change_of_state.__name__ == State.APPLIED:
                checks_before_apply(instance.user, instance.job)

            try:
                change_of_state(instance)
            except django_fsm.TransitionNotAllowed:
                raise ValidationError(
                    "Can't switch from state {0} TO {1} ".format(instance.state, state)
                )
            if instance.state == State.APPLIED:
                debit_tokens_from_user(instance.user, instance.job.required_tokens)

            instance._extra_data = request.data
            instance._request_user = request.user
            instance.save()

            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            raise ValidationError(
                "Please provide a state to update application status."
            )


class MobileAppVersionView(generics.ListAPIView):
    """Upgrade mobile app."""

    serializer_class = MobileAppVersionSerializer
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """Get android application version details by id."""
        version_code = int(kwargs.get("version_code", None))
        app_type = request.GET.get("app_type", choices.TALENT)
        version_object = MobileAppVersion.objects.filter(
            version_code__gte=version_code, app_type=app_type
        ).last()

        if version_object and version_code == version_object.version_code:
            return Response(
                {
                    "version_code": version_object.version_code,
                    "is_required": False,
                    "url": version_object.url,
                    "message": version_object.message,
                    "app_type": version_object.app_type,
                }
            )
        serializer = self.get_serializer(version_object)

        return Response(serializer.data)


class CheckUserProfileInfo(generics.ListAPIView):
    def get(self, request, job_id=None, **kwargs):
        user = request.user
        if job_id:
            try:
                Job.objects.get(pk=job_id)
            except Job.DoesNotExist:
                raise NotFound("Job with job id {} does not exist.".format(job_id))
        result = check_person_information(user.person)
        if False in result.values():
            raise ValidationError(result)
        return Response({"results": "Profile data enough to apply to job."})


class MultipleApplicationsViewSet(generics.CreateAPIView):

    serializer_class = ApplicationSerializer
    permission_classes = (IsCastingDirector,)

    def post(self, request, *args, **kwargs):
        """Change multiple application states. If invited send notifications."""
        data = request.data.copy()
        application_ids = data.keys()
        result = {}
        applications = []
        for application_id in application_ids:
            applications.extend(
                Application.objects.filter(
                    job__id=data[application_id]["job_id"], id=application_id
                )
            )

        for application in applications:
            application_id = str(application.id)
            state = data[application_id]["state"]
            if application.state == State.APPLIED and state == State.INVITED:
                change_of_state = getattr(Application, "direct_invited")
            else:
                try:
                    change_of_state = getattr(Application, state)
                except AttributeError:
                    result[application.id] = {
                        "error": "Application state can not be {}".format(state),
                        "user_id": application.user.id,
                    }
                    continue
            try:
                change_of_state(application)
                application._extra_data = request.data[application_id]
                application._request_user = request.user
                application.save()
                result[application_id] = "sucess"
            except django_fsm.TransitionNotAllowed:
                result[application.id] = {
                    "error": "Can't switch from state {0} TO {1} ".format(
                        application.state, state
                    ),
                    "user_id": application.user.id,
                }
        return Response(result)


class MultipleUsersViewSet(generics.CreateAPIView):

    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated,)

    acceptable_target_states = [State.SHORTLISTED, State.INVITED, State.REJECTED]
    action = {
        "rejected": "agent_rejected",
        "shortlisted": "shortlisted",
        "invited": "direct_invited",
    }

    def _validate_target_state(self, target_state):
        if not target_state:
            raise ValidationError("Target state is required to perform this action.")
        if target_state not in self.acceptable_target_states:
            raise ValidationError(
                "States can be {} only.".format(self.acceptable_target_states)
            )

    def post(self, request, *args, **kwargs):
        """Change multiple application states. If invited send notifications."""
        data = request.data.copy()
        user_ids = data.get("user_ids")
        if not user_ids:
            raise ("user_ids are required to perform action.")
        result = {"errors": [], "sucess": []}
        users = User.objects.filter(id__in=user_ids)
        job = Job.objects.get(id=kwargs.get("job_id"))
        for user in users:
            target_state = data.get("state")

            self._validate_target_state(target_state)

            application, created = Application.objects.get_or_create(user=user, job=job)

            if application.state == State.SHORTLISTED and target_state == State.INVITED:
                change_of_state = getattr(Application, "invited")
            else:
                try:
                    change_of_state = getattr(Application, self.action[target_state])
                except AttributeError:
                    result[user.id] = {
                        "error": "Application state can not be {}".format(self.action),
                        "user_id": user.id,
                    }
                    continue
            try:

                bound_method = change_of_state.__dict__["__wrapped__"].__get__(
                    application, Application
                )

                if not has_transition_perm(bound_method, request.user):
                    result["errors"].append(
                        {
                            "detail": "You do not have permission to change state from {} TO {}".format(
                                application.state, target_state
                            ),
                            "user_id": user.id,
                        }
                    )
                    continue
                change_of_state(application)
                application._extra_data = request.data
                application._request_user = request.user
                application.save()
                result["sucess"].append(
                    {"application_id": application.id, "user_id": user.id}
                )
            except django_fsm.TransitionNotAllowed:
                result["errors"].append(
                    {
                        "detail": "Can't switch from state {0} TO {1} ".format(
                            application.state, target_state
                        ),
                        "user_id": user.id,
                    }
                )

        return Response(result)
