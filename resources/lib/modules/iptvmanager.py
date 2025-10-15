# -*- coding: utf-8 -*-
"""Implementation of IPTVManager class"""

import logging
from datetime import datetime, timedelta

from resources.lib import kodiutils
from resources.lib.play.auth import AuthApi
from resources.lib.play.content import ContentApi
from resources.lib.play.epg import EpgApi

_LOGGER = logging.getLogger(__name__)


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port
        auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(auth, cache_path=kodiutils.get_cache_path())

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            import json
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):  # pylint: disable=no-method-argument
        """Return JSON-STREAMS formatted information to IPTV Manager"""
        streams = []
        channels = self._api.get_live_channels()
        for channel in channels:
            if channel.uuid:
                streams.append({
                    'id': channel.uuid,
                    'name': channel.title,
                    'logo': channel.logo,
                    'stream': 'plugin://plugin.video.play/play/catalog/{uuid}/live_channel'.format(uuid=channel.uuid),
                    'vod': 'plugin://plugin.video.play/play/epg/{channel}/{{date}}'.format(channel=channel.uuid)
                })

        return {'version': 1, 'streams': streams}

    @via_socket
    def send_epg(self):  # pylint: disable=no-method-argument
        """Return JSON-EPG formatted information to IPTV Manager"""
        epg_api = EpgApi()

        today = datetime.today()

        results = {}
        channels = self._api.get_live_channels()
        for channel in channels:
            uuid = channel.uuid

            if channel.uuid:
                results[uuid] = []

                for i in range(-3, 7):
                    date = today + timedelta(days=i)
                    epg = epg_api.get_epg(channel.title.lower().split()[-1], date.strftime('%Y-%m-%d'))

                    results[uuid].extend([
                        {
                            'start': program.start.isoformat(),
                            'stop': (program.start + timedelta(seconds=program.duration)).isoformat(),
                            'title': program.program_title,
                            'subtitle': program.episode_title,
                            'description': program.description,
                            'episode': 'S%sE%s' % (program.season, program.number) if program.season and program.number else None,
                            'genre': program.genre,
                            'genre_id': program.genre_id,
                            'image': program.thumb,
                            'stream': kodiutils.url_for('play_catalog',
                                                        uuid=program.video_url) if program.video_url else None
                        }
                        for program in epg if program.duration
                    ])

        return {'version': 1, 'epg': results}
