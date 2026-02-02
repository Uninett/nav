import logging

from django.contrib.auth.backends import RemoteUserBackend

from nav.auditlog.models import LogEntry
from nav.web.auth import remote_user


_logger = logging.getLogger(__name__)


class NAVRemoteUserBackend(RemoteUserBackend):
    def __init__(self):
        self.create_unknown_user = remote_user.CONFIG.will_autocreate_user()

    def authenticate(self, request, user):
        if not remote_user.CONFIG.is_remote_user_enabled():
            return None

        user = super().authenticate(request, user)
        return user

    def clean_username(self, username):
        return remote_user.CONFIG.clean_username(username)

    def configure_user(self, request, user, created=True):
        if created:
            # for the sake of Account.locked
            user.set_password(remote_user.fake_password(32))
            user.ext_sync = 'REMOTE_USER'
            user.save()

            remote_user_varname = remote_user.CONFIG.get_remote_user_varname()
            _logger.info(
                "Created user %s from header %s",
                user.get_username(),
                remote_user_varname,
            )
            template = (
                'Account "{actor}" created due to {remote_user_varname} HTTP header'
            )
            LogEntry.add_log_entry(
                user, 'create-account', template=template, subsystem='auth'
            )
        return user

    def user_can_authenticate(self, user):
        active = super().user_can_authenticate(user)

        if not active:
            _logger.info("Locked user %s tried to log in", user.get_username())
            template = 'Account "{actor}" was prevented from logging in: blocked'
            LogEntry.add_log_entry(
                user, 'login-prevent', template=template, subsystem='auth'
            )

        return active
