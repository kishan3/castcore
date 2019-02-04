"""Custom Backend for login using phone number and email."""
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import check_password
from rest_framework.exceptions import NotFound, AuthenticationFailed


class CustomAuthBackend(object):
    """Custom Email Backend to perform authentication via email."""

    def authenticate(self, email=None, password=None, **kwargs):
        """Authenticate user based on email or phone number."""
        my_user_model = get_user_model()
        try:
            if email:
                user = my_user_model.objects.get(email=email)
            elif kwargs.get('username'):
                user = my_user_model.objects.get(email=kwargs.get('username'))
            elif kwargs.get("phone"):
                user = my_user_model.objects.get(phone=kwargs.get('phone'))
        except my_user_model.DoesNotExist:
            raise NotFound("user does not exist.")
        except Exception as e:
            raise e

        if user.check_password(password):
            return user
        raise AuthenticationFailed("Invalid credentials given.")

    def get_user(self, user_id):
        """Get user object based on its id."""
        my_user_model = get_user_model()
        try:
            return my_user_model.objects.get(pk=user_id)
        except my_user_model.DoesNotExist:
            raise NotFound("user does not exist.")
