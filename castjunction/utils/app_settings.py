class AppSettings(object):
    class AuthenticationMethod:
        USERNAME = "username"
        EMAIL = "email"
        USERNAME_EMAIL = "username_email"
        USERNAME_EMAIL_PHONE = "username_email_phone"

    class EmailVerificationMethod:
        # After signing up, keep the user account inactive until the email
        # address is verified
        MANDATORY = "mandatory"
        # Allow login with unverified e-mail (e-mail verification is
        # still sent)
        OPTIONAL = "optional"
        # Don't send e-mail verification mails during signup
        NONE = "none"

    def __init__(self, prefix):
        self.prefix = prefix
        # If login is by email, email must be required
        assert (
            not self.AUTHENTICATION_METHOD == self.AuthenticationMethod.EMAIL
        ) or self.EMAIL_REQUIRED
        # If login includes email, login must be unique
        assert (
            self.AUTHENTICATION_METHOD == self.AuthenticationMethod.USERNAME
        ) or self.UNIQUE_EMAIL
        assert (
            self.EMAIL_VERIFICATION != self.EmailVerificationMethod.MANDATORY
        ) or self.EMAIL_REQUIRED
        if not self.USER_MODEL_USERNAME_FIELD:
            assert not self.USERNAME_REQUIRED
            assert self.AUTHENTICATION_METHOD not in (
                self.AuthenticationMethod.USERNAME,
                self.AuthenticationMethod.USERNAME_EMAIL,
            )

    def _setting(self, name, dflt):
        from django.conf import settings

        getter = getattr(
            settings,
            "ALLAUTH_SETTING_GETTER",
            lambda name, dflt: getattr(settings, name, dflt),
        )
        return getter(self.prefix + name, dflt)

    @property
    def DEFAULT_HTTP_PROTOCOL(self):
        return self._setting("DEFAULT_HTTP_PROTOCOL", "http").lower()

    @property
    def EMAIL_CONFIRMATION_EXPIRE_DAYS(self):
        """
        Determines the expiration date of e-mail confirmation mails (#
        of days)
        """
        from django.conf import settings

        return self._setting(
            "EMAIL_CONFIRMATION_EXPIRE_DAYS",
            getattr(settings, "EMAIL_CONFIRMATION_DAYS", 3),
        )

    @property
    def EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL(self):
        """
        The URL to redirect to after a successful e-mail confirmation, in
        case of an authenticated user
        """
        return self._setting("EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL", None)

    @property
    def EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL(self):
        """
        The URL to redirect to after a successful e-mail confirmation, in
        case no user is logged in
        """
        from django.conf import settings

        return self._setting(
            "EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL", settings.LOGIN_URL
        )

    @property
    def EMAIL_REQUIRED(self):
        """
        The user is required to hand over an e-mail address when signing up
        """
        return self._setting("EMAIL_REQUIRED", True)

    @property
    def EMAIL_VERIFICATION(self):
        """
        See e-mail verification method
        """
        ret = self._setting("EMAIL_VERIFICATION", self.EmailVerificationMethod.OPTIONAL)
        # Deal with legacy (boolean based) setting
        if ret is True:
            ret = self.EmailVerificationMethod.MANDATORY
        elif ret is False:
            ret = self.EmailVerificationMethod.OPTIONAL
        return ret

    @property
    def AUTHENTICATION_METHOD(self):
        from django.conf import settings

        if hasattr(settings, "ACCOUNT_EMAIL_AUTHENTICATION"):
            import warnings

            warnings.warn(
                "ACCOUNT_EMAIL_AUTHENTICATION is deprecated,"
                " use ACCOUNT_AUTHENTICATION_METHOD",
                DeprecationWarning,
            )
            if getattr(settings, "ACCOUNT_EMAIL_AUTHENTICATION"):
                ret = self.AuthenticationMethod.EMAIL
            else:
                ret = self.AuthenticationMethod.USERNAME_EMAIL_PHONE
        else:
            ret = self.AuthenticationMethod.USERNAME_EMAIL_PHONE
        return ret

    @property
    def UNIQUE_EMAIL(self):
        """
        Enforce uniqueness of e-mail addresses
        """
        return self._setting("UNIQUE_EMAIL", True)

    @property
    def SIGNUP_PASSWORD_VERIFICATION(self):
        """
        Signup password verification
        """
        return self._setting("SIGNUP_PASSWORD_VERIFICATION", True)

    @property
    def PASSWORD_MIN_LENGTH(self):
        """
        Minimum password Length
        """
        return self._setting("PASSWORD_MIN_LENGTH", 6)

    @property
    def EMAIL_SUBJECT_PREFIX(self):
        """
        Subject-line prefix to use for email messages sent
        """
        return self._setting("EMAIL_SUBJECT_PREFIX", None)

    @property
    def SIGNUP_FORM_CLASS(self):
        """
        Signup form
        """
        return self._setting("SIGNUP_FORM_CLASS", None)

    @property
    def USERNAME_REQUIRED(self):
        """
        The user is required to enter a username when signing up
        """
        return self._setting("USERNAME_REQUIRED", False)

    @property
    def USERNAME_MIN_LENGTH(self):
        """
        Minimum username Length
        """
        return self._setting("USERNAME_MIN_LENGTH", 1)

    @property
    def USERNAME_BLACKLIST(self):
        """
        List of usernames that are not allowed
        """
        return self._setting("USERNAME_BLACKLIST", [])

    @property
    def PASSWORD_INPUT_RENDER_VALUE(self):
        """
        render_value parameter as passed to PasswordInput fields
        """
        return self._setting("PASSWORD_INPUT_RENDER_VALUE", False)

    @property
    def ADAPTER(self):
        return self._setting("ADAPTER", "allauth.account.adapter.DefaultAccountAdapter")

    @property
    def CONFIRM_EMAIL_ON_GET(self):
        return self._setting("CONFIRM_EMAIL_ON_GET", False)

    @property
    def AUTHENTICATED_LOGIN_REDIRECTS(self):
        return self._setting("AUTHENTICATED_LOGIN_REDIRECTS", True)

    @property
    def LOGIN_ON_EMAIL_CONFIRMATION(self):
        """
        Automatically log the user in once they confirmed their email address
        """
        return self._setting("LOGIN_ON_EMAIL_CONFIRMATION", False)

    @property
    def LOGIN_ON_PASSWORD_RESET(self):
        """
        Automatically log the user in immediately after resetting
        their password.
        """
        return self._setting("LOGIN_ON_PASSWORD_RESET", False)

    @property
    def LOGOUT_REDIRECT_URL(self):
        return self._setting("LOGOUT_REDIRECT_URL", "/")

    @property
    def LOGOUT_ON_GET(self):
        return self._setting("LOGOUT_ON_GET", False)

    @property
    def LOGOUT_ON_PASSWORD_CHANGE(self):
        return self._setting("LOGOUT_ON_PASSWORD_CHANGE", False)

    @property
    def USER_MODEL_USERNAME_FIELD(self):
        return self._setting("USER_MODEL_USERNAME_FIELD", "username")

    @property
    def USER_MODEL_EMAIL_FIELD(self):
        return self._setting("USER_MODEL_EMAIL_FIELD", "email")

    @property
    def SESSION_COOKIE_AGE(self):
        """
        Deprecated -- use Django's settings.SESSION_COOKIE_AGE instead
        """
        from django.conf import settings

        return self._setting("SESSION_COOKIE_AGE", settings.SESSION_COOKIE_AGE)

    @property
    def SESSION_REMEMBER(self):
        """
        Controls the life time of the session. Set to `None` to ask the user
        ("Remember me?"), `False` to not remember, and `True` to always
        remember.
        """
        return self._setting("SESSION_REMEMBER", None)

    @property
    def TEMPLATE_EXTENSION(self):
        """
        A string defining the template extension to use, defaults to `html`.
        """
        return self._setting("TEMPLATE_EXTENSION", "html")

    @property
    def FORMS(self):
        return self._setting("FORMS", {})

    @property
    def LOGIN_ATTEMPTS_LIMIT(self):
        """
        Number of failed login attempts. When this number is
        exceeded, the user is prohibited from logging in for the
        specified `LOGIN_ATTEMPTS_TIMEOUT`
        """
        return self._setting("LOGIN_ATTEMPTS_LIMIT", 5)

    @property
    def LOGIN_ATTEMPTS_TIMEOUT(self):
        """
        Time period from last unsuccessful login attempt, during
        which the user is prohibited from trying to log in.  Defaults to
        5 minutes.
        """
        return self._setting("LOGIN_ATTEMPTS_TIMEOUT", 60 * 5)


# Ugly? Guido recommends this himself ...
# http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
import sys

app_settings = AppSettings("ACCOUNT_")
app_settings.__name__ = __name__
sys.modules[__name__] = app_settings
