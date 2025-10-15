# -*- coding: utf-8 -*-
""" Channels module """

import logging

from resources.lib import kodiutils
from resources.lib.play import STREAM_DICT
from resources.lib.play.auth import AuthApi
from resources.lib.play.content import ContentApi

_LOGGER = logging.getLogger(__name__)


class Channels:
    """ Menu code related to channels """

    def __init__(self):
        """ Initialise object """
        if not kodiutils.has_credentials():
            kodiutils.open_settings()
        self._auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(self._auth, cache_path=kodiutils.get_cache_path())

    def show_channels(self):
        """ Shows TV channels """
        try:
            items = self._api.get_live_channels()
        except Exception as ex:
            kodiutils.notification(message=str(ex))
            raise

        listing = []

        for channel in items:

            listing.append(
                kodiutils.TitleItem(
                    title=channel.title,
                    path=kodiutils.url_for('show_channel_menu', uuid=channel.uuid),
                    art_dict={
                        'icon': channel.logo,
                        'thumb': channel.logo,
                        'fanart': channel.fanart,
                    },
                    info_dict={
                        'plot': None,
                        'playcount': 0,
                        'mediatype': 'video',
                    },
                    stream_dict=STREAM_DICT,
                ),
            )

        kodiutils.show_listing(listing, 30007)

    def show_channel_menu(self, uuid):
        """ Shows a TV channel
        :type uuid: str
        """
        try:
            items = self._api.get_live_channels()
        except Exception as ex:
            kodiutils.notification(message=str(ex))
            raise

        channel = next(channel for channel in items if channel.uuid == uuid)

        listing = []

 #       if channel.get('epg_id'):
        listing.append(
            kodiutils.TitleItem(
                title=kodiutils.localize(30053, channel=channel.title),  # TV Guide for {channel}
                path=kodiutils.url_for('show_channel_tvguide', channel=channel.title),
                art_dict={
                    'icon': 'DefaultAddonTvInfo.png',
                    'fanart': channel.fanart,
                },
                info_dict={
                    'plot': kodiutils.localize(30054, channel=channel.title),  # Browse the TV Guide for {channel}
                }
            )
        )


        listing.append(
            kodiutils.TitleItem(
                title=kodiutils.localize(30055, channel=channel.title),  # Catalog for {channel}
                path=kodiutils.url_for('show_channel_catalog', channel=channel.brand.lower()),
                art_dict={
                    'icon': 'DefaultMovieTitle.png',
                    'fanart': channel.fanart,
                },
                info_dict={
                    'plot': kodiutils.localize(30056, channel=channel.title),  # Browse the Catalog for {channel}
                }
            )
        )

        listing.append(
            kodiutils.TitleItem(
                title=kodiutils.localize(30052, channel=channel.title),  # Watch live {channel}
                path=kodiutils.url_for('play_catalog', uuid=channel.uuid, content_type='live_channel') + '?.pvr',
                art_dict={
                    'icon': channel.logo,
                    'fanart': channel.fanart,
                },
                info_dict={
                    'plot': kodiutils.localize(30052, channel=channel.title),  # Watch live {channel}
                    'playcount': 0,
                    'mediatype': 'video',
                },
                is_playable=True,
            )
        )

        kodiutils.show_listing(listing, 30007, sort=['unsorted'])
