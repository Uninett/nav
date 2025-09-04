import logging

from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import reverse
from django.utils.http import urlencode

from social_core.pipeline.partial import partial


_logger = logging.getLogger(__name__)


@partial
def require_password(strategy, details, user=None, is_new=False, *args, **kwargs):
    _logger.debug("Login via PSA: start")
    if kwargs.get("ajax"):
        return None

    if not is_new or not user or user.is_active:
        _logger.debug("Login via PSA: old user")
        return None

    # From this point: We have a new user and the user has no password yet

    form = SetPasswordForm(user, strategy.request_data())
    if form.is_valid():
        assert False, 'done!'
        _logger.debug("Login via PSA: password set, done!")
        form.save()  # password is correctly saved on user
        return None

    current_partial = kwargs.get("current_partial")
    base_url = reverse(
        'psa-require-password',
        kwargs={"backend": current_partial.backend, "user_id": user.id},
    )
    params = urlencode({'partial_token': current_partial.token})
    url = '{}?{}'.format(base_url, params)
    _logger.debug("Login via PSA: redirect to password form")
    return strategy.redirect(url)
