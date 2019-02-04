"""Custom adapter for users app."""
import requests
from io import BytesIO
import urllib
import uuid

from django.core.files.images import ImageFile
from allauth.exceptions import ImmediateHttpResponse
from allauth.account.models import EmailAddress
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.adapter import get_adapter as get_account_adapter

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount import providers
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter, compute_appsecret_proof
from allauth.socialaccount.providers.facebook.provider import FacebookProvider, GRAPH_API_URL
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter, TwitterAPI
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount import signals
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import AuthProcess
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import (_social_login_redirect,
                                           _add_social_account,
                                           _process_signup,
                                           _login_social_account)

from multimedia.models import Image
from .models import Person, Company, User


def _complete_social_login(request, sociallogin, response):
    if request.user.is_authenticated():
        get_account_adapter().logout(request)
    if sociallogin.is_existing:
        # Login existing user
        ret = _login_social_account(request, sociallogin)
    else:
        # New social user
        ret = _process_signup(request, sociallogin)
        try:
            url = response['profile_image_url']
        except Exception:
            url = response.get('picture')
            if type(url) is dict:
                # Incase of facebook response dict is different.
                url = response.get('picture').get('data').get('url')
        if url:
            url = urllib.request.urlopen(url)
            file = BytesIO(url.read())
            img = ImageFile(file)
            filename = '%s_original.jpg' % (uuid.uuid4())
            img.name = filename
            # ser = ImageSerializer(img)
            Image.objects.create(
                image=img,
                title=img.name,
                content_object=sociallogin.user,
                object_id=sociallogin.user.id,
                image_type='P')
    return ret


def complete_social_login(request, sociallogin, response):
    """Custom call to _complete_social_login."""
    assert not sociallogin.is_existing
    sociallogin.lookup()
    try:
        get_adapter(request).pre_social_login(request, sociallogin)
        signals.pre_social_login.send(sender=SocialLogin,
                                      request=request,
                                      sociallogin=sociallogin)
    except ImmediateHttpResponse as e:
        return e.response
    process = sociallogin.state.get('process')
    if process == AuthProcess.REDIRECT:
        return _social_login_redirect(request, sociallogin)
    elif process == AuthProcess.CONNECT:
        return _add_social_account(request, sociallogin)
    else:
        return _complete_social_login(request, sociallogin, response)


def sociallogin_from_response(self, request, response, **kwargs):
    """Custom sociallogin from user for person and company models."""
    from allauth.socialaccount.models import SocialLogin, SocialAccount
    adapter = SocialAccountAdapter()
    uid = self.extract_uid(response)
    extra_data = self.extract_extra_data(response)
    common_fields = self.extract_common_fields(response)
    socialaccount = SocialAccount(extra_data=extra_data,
                                  uid=uid,
                                  provider=self.id)
    email_addresses = self.extract_email_addresses(response)
    self.cleanup_email_addresses(common_fields.get('email'),
                                 email_addresses)
    sociallogin = SocialLogin(account=socialaccount,
                              email_addresses=email_addresses)
    # user = sociallogin.user = adapter.new_user(request, sociallogin)
    from .serializers import RegisterSerializer
    data = RegisterSerializer().validate_account_type(account_type=extra_data['account_type'])

    if 'C' in data.keys():
        user = sociallogin.user = Company()
        user.user_type = User.COMPANY
    else:
        user = sociallogin.user = Person()

    user.set_unusable_password()
    adapter.populate_user(request, sociallogin, common_fields)

    return sociallogin, response


def fb_complete_login(request, app, token, **kwargs):
    """Custom fb login."""
    provider = providers.registry.by_id(FacebookProvider.id)
    resp = requests.get(
        GRAPH_API_URL + '/me',
        params={
            'fields': ','.join(provider.get_fields()),
            'access_token': token.token,
            'appsecret_proof': compute_appsecret_proof(app, token)
        })
    resp.raise_for_status()
    extra_data = resp.json()
    extra_data.update({'account_type': kwargs.get('account_type')})
    login, response = sociallogin_from_response(provider, request=request, response=extra_data)
    return login, response


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social login adapter."""

    def pre_social_login(self, request, sociallogin):
        """Get called after user is authorized and before sign up.

        It checks for existing user and connects if user is already signed up.
        """
        # Taken from: http://stackoverflow.com/a/30591838/2286762
        user = sociallogin.user
        if sociallogin.is_existing:
            return

        # some social logins don't have an email address, e.g. facebook accounts
        # with mobile numbers only, but allauth takes care of this case so just
        # ignore it
        if 'email' not in sociallogin.account.extra_data:
            return

        # check if given email address already exists.
        # Note: __iexact is used to ignore cases
        try:
            email = sociallogin.account.extra_data['email'].lower()
            email_address = EmailAddress.objects.get(email__iexact=email)

        # if it does not, let allauth take care of this new social account
        except EmailAddress.DoesNotExist:
            return

        # if it does, connect this new social login to the existing user
        user = email_address.user
        sociallogin.connect(request, user)


class FacebookOAuth2AdapterFixed(FacebookOAuth2Adapter):
    """Custom facebook adapter."""

    def __init__(self):
        """Init."""
        pass

    def complete_login(self, request, app, access_token, **kwargs):
        """Custom complete login for facebook sign up."""
        return fb_complete_login(request, app, access_token, **kwargs)


class TwitterOAuth2AdapterFixed(TwitterOAuthAdapter):
    """Custom twitter adapter."""

    def __init__(self):
        """Init."""
        pass

    def complete_login(self, request, app, token, response, **kwargs):
        """Custom complete login for twitter sign up."""
        client = TwitterAPI(request, app.client_id, app.secret,
                            self.request_token_url)
        extra_data = client.get_user_info()
        provider = self.get_provider()
        extra_data.update({'account_type': kwargs.get('account_type')})
        return sociallogin_from_response(provider, request=request, response=extra_data)


class GoogleOAuth2AdapterFixed(GoogleOAuth2Adapter):
    """Custom google adapter."""

    def __init__(self):
        """Init."""
        pass

    def complete_login(self, request, app, token, **kwargs):
        """Custom complete login for google sign up."""
        resp = requests.get(self.profile_url,
                            params={'access_token': token.token,
                                    'alt': 'json'})
        resp.raise_for_status()
        extra_data = resp.json()
        provider = self.get_provider()
        extra_data.update({'account_type': kwargs.get('account_type')})
        login, response = sociallogin_from_response(provider, request=request, response=extra_data)
        return login, response


class MyAccountAdapter(DefaultAccountAdapter):

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        pass
