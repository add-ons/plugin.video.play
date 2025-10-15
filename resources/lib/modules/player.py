# -*- coding: utf-8 -*-
""" Player module """

import logging

from resources.lib import kodiutils
from resources.lib.play.auth import AuthApi
from resources.lib.play.aws.cognito_idp import AuthenticationException, InvalidLoginException
from resources.lib.play.content import ApiException, ContentApi, GeoblockedException, MissingModuleException, UnavailableException

_LOGGER = logging.getLogger(__name__)


class Player:
    """ Code responsible for playing media """

    def __init__(self):
        """ Initialise object """
        auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(auth, cache_path=kodiutils.get_cache_path())

        # Workaround for Raspberry Pi 3 and older
        kodiutils.set_global_setting('videoplayer.useomxplayer', True)

    def play(self, uuid, content_type):
        """ Play the requested item.
        :type uuid: str
        :type content_type: str
        """
        if not uuid:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            return

        # Lookup the stream
        resolved_stream = self._resolve_stream(uuid, content_type)
        if resolved_stream:
            kodiutils.play(resolved_stream.url, resolved_stream.stream_type, resolved_stream.license_key)
        return

    @staticmethod
    def check_credentials():
        """ Check if we have credentials
        :rtype bool
        """
        if not kodiutils.get_setting('username') or not kodiutils.get_setting('password'):
            confirm = kodiutils.yesno_dialog(
                message=kodiutils.localize(30701))  # To watch a video, you need to enter your credentials. Do you want to enter them now?
            if confirm:
                kodiutils.open_settings()
            kodiutils.end_of_directory()
            return False
        return True

    def _resolve_stream(self, uuid, content_type):  # pylint: disable=too-many-return-statements
        """ Resolve the stream for the requested item
        :type uuid: str
        :type content_type: str
        """
        if self.check_credentials():
            # Fetch an auth token now
            try:
                auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())

            except (InvalidLoginException, AuthenticationException) as ex:
                _LOGGER.exception(ex)
                kodiutils.ok_dialog(message=kodiutils.localize(30702, error=str(ex)))
                kodiutils.end_of_directory()
                return None

            try:
                # Get stream information
                resolved_stream = ContentApi(auth).get_stream(uuid, content_type)
                return resolved_stream

            except GeoblockedException as ex:
                kodiutils.ok_dialog(message=kodiutils.localize(30710, error=str(ex)))  # This video is geo-blocked...
                kodiutils.end_of_directory()
                return None

            except UnavailableException:
                kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
                kodiutils.end_of_directory()
                return None

            except MissingModuleException as ex:
                kodiutils.ok_dialog(message=kodiutils.localize(30721, error=str(ex)))  # You need to install an extra Python module...
                kodiutils.end_of_directory()
                return None

            except ApiException as ex:
                kodiutils.ok_dialog(message=kodiutils.localize(30722, error=str(ex)))  # The server returned an error...
                kodiutils.end_of_directory()
                return None

        kodiutils.end_of_directory()
        return None
