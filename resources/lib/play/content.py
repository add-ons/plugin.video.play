# -*- coding: utf-8 -*-
""" CONTENT API """

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

from resources.lib import kodiutils
from resources.lib.play import utils
from resources.lib.play import ResolvedStream
from resources.lib.play.exceptions import NoContentException, UnavailableException
from resources.lib.kodiutils import STREAM_DASH, STREAM_HLS, html_to_kodi
from resources.lib.drm import get_license_keys, get_pssh_box

_LOGGER = logging.getLogger(__name__)

CACHE_AUTO = 1  # Allow to use the cache, and query the API if no cache is available
CACHE_ONLY = 2  # Only use the cache, don't use the API
CACHE_PREVENT = 3  # Don't use the cache


class Program:
    """ Defines a Program. """

    def __init__(self, uuid=None, path=None, channel=None, category_id=None, category_name=None, title=None, description=None, aired=None, expiry=None, poster=None, thumb=None, fanart=None, seasons=None,
                 my_list=False):
        """
        :type uuid: str
        :type path: str
        :type channel: str
        :type category_id: str
        :type category_name: str
        :type title: str
        :type description: str
        :type aired: datetime
        :type expiry: datetime
        :type poster: str
        :type thumb: str
        :type fanart: str
        :type seasons: list[Season]
        :type my_list: bool
        """
        self.uuid = uuid
        self.path = path
        self.channel = channel
        self.category_id = category_id
        self.category_name = category_name
        self.title = title
        self.description = description
        self.aired = aired
        self.expiry = expiry
        self.poster = poster
        self.thumb = thumb
        self.fanart = fanart
        self.seasons = seasons
        self.my_list = my_list

    def __repr__(self):
        return "%r" % self.__dict__


class Season:
    """ Defines a Season. """

    def __init__(self, uuid=None, path=None, channel=None, title=None, description=None, number=None):
        """
        :type uuid: str
        :type path: str
        :type channel: str
        :type title: str
        :type description: str
        :type number: int

        """
        self.uuid = uuid
        self.path = path
        self.channel = channel
        self.title = title
        self.description = description
        self.number = number

    def __repr__(self):
        return "%r" % self.__dict__


class Episode:
    """ Defines an Episode. """

    def __init__(self, uuid=None, nodeid=None, path=None, channel=None, program_title=None, title=None, description=None, thumb=None, duration=None,
                 position=None, season=None, season_uuid=None, number=None, rating=None, aired=None, expiry=None, stream=None, content_type=None):
        """
        :type uuid: str
        :type nodeid: str
        :type path: str
        :type channel: str
        :type program_title: str
        :type title: str
        :type description: str
        :type thumb: str
        :type duration: int
        :type position: int
        :type season: int
        :type season_uuid: str
        :type number: int
        :type rating: str
        :type aired: datetime
        :type expiry: datetime
        :type stream: str
        :type content_type: str
        """
        self.uuid = uuid
        self.nodeid = nodeid
        self.path = path
        self.channel = channel
        self.program_title = program_title
        self.title = title
        self.description = description
        self.thumb = thumb
        self.duration = duration
        self.position = position
        self.season = season
        self.season_uuid = season_uuid
        self.number = number
        self.rating = rating
        self.aired = aired
        self.expiry = expiry
        self.stream = stream
        self.content_type = content_type

    def __repr__(self):
        return "%r" % self.__dict__


class Category:
    """ Defines a Category. """

    def __init__(self, uuid=None, channel=None, title=None, programs=None, episodes=None):
        """
        :type uuid: str
        :type channel: str
        :type title: str
        :type programs: List[Program]
        :type episodes: List[Episode]
        """
        self.uuid = uuid
        self.channel = channel
        self.title = title
        self.programs = programs
        self.episodes = episodes

    def __repr__(self):
        return "%r" % self.__dict__


class Swimlane:
    """ Defines a Swimlane. """

    def __init__(self, index=None, title=None, lane_type=None):
        """
        :type index: int
        :type title: str
        :type lane_type: str
        """
        self.index = index
        self.title = title
        self.lane_type = lane_type

    def __repr__(self):
        return "%r" % self.__dict__


class Channel:
    """ Defines a Channel. """

    def __init__(self, uuid=None, index=None, title=None, description=None, brand=None, logo=None, fanart=None):
        """
        :type uuid: str
        :type index: int
        :type title: str
        :type description: str
        :type brand: str
        :type logo: str
        :type fanart: str
        """
        self.uuid = uuid
        self.index = index
        self.title = title
        self.description = description
        self.brand = brand
        self.logo = logo
        self.fanart = fanart


    def __repr__(self):
        return "%r" % self.__dict__


class ContentApi:
    """ Play Content API"""
    SITE_URL = 'https://www.play.tv'
    API_PLAY = 'https://api.play.tv'
    LICENSE_URL = 'https://widevine.keyos.com/api/v4/getLicense'

    def __init__(self, auth=None, cache_path=None):
        """ Initialise object """
        self._auth = auth
        self._cache_path = cache_path

    def get_programs(self, channel=None, category=None):
        """ Get all programs optionally filtered by channel or category.
        :type channel: str
        :type category: int
        :rtype list[Program]
        """
        programs = self.get_program_tree()

        # Return all programs
        if not channel and not category:
            return programs

        # filter by category_id, channel
        key = ''
        value = None
        if channel:
            key = 'channel'
            value = channel
        elif category:
            key = 'category_id'
            value = category
        return [program for program in programs if getattr(program, key) == value]

    def get_program(self, uuid, cache=CACHE_AUTO):
        """ Get a Program object with the specified uuid.
        :type uuid: str
        :type cache: str
        :rtype Program
        """
        if not uuid:
            return None

        def update():
            """ Fetch the program metadata """
            # Fetch webpage
            result = utils.get_url(self.API_PLAY + '/tv/v2/programs/%s' % uuid)
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['program', uuid], cache_mode=cache, update=update)
        if not data:
            return None

        program = self._parse_program_data(data)

        return program

    def get_live_channels(self, cache=CACHE_AUTO):
        """  Get a list of live channels.
        :type cache: str
        :rtype list[Channel]
        """
        def update():
            """ Fetch the program metadata """
            # Fetch webpage
            result = utils.get_url(self.API_PLAY + '/tv/v1/liveStreams', authentication='Bearer %s' % self._auth.get_token())
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['channels'], cache_mode=cache, update=update)
        if not data:
            raise NoContentException('No content')

        channels = self._parse_channels_data(data)

        return channels

    def get_episodes(self, playlist_uuid, offset=0, limit=100, cache=CACHE_AUTO):
        """  Get a list of all episodes of the specified playlist.
        :type playlist_uuid: str
        :type cache: str
        :rtype list[Episode]
        """
        if not playlist_uuid:
            return None

        def update():
            """ Fetch the program metadata """
            # Fetch webpage
            result = utils.get_url(self.API_PLAY + '/tv/v1/playlists/%s?offset=%s&limit=%s' % (playlist_uuid, offset, limit), authentication='Bearer %s' % self._auth.get_token())
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['playlist', playlist_uuid, offset, limit], cache_mode=cache, update=update)
        if not data:
            return None

        episodes = self._parse_playlist_data(data)

        return episodes

    def get_stream(self, uuid: str, content_type: str) -> ResolvedStream:
        """
        Return a ResolvedStream for this video.

        :param uuid: Unique ID of the video
        :param content_type: Video type, e.g. 'video-short_form', 'live_channel'
        :return: ResolvedStream
        :raises UnavailableException: if the stream data cannot be retrieved
        """
        # Determine mode based on content type
        mode_map = {
            'video-short_form': 'videos/short-form',
            'live_channel': 'liveStreams',
        }
        mode = mode_map.get(content_type, 'videos/long-form')

        # Fetch stream info
        url = f"{self.API_PLAY}/tv/v1/{mode}/{uuid}"
        token = self._auth.get_token()
        response = utils.get_url(url, authentication=f"Bearer {token}")
        data = json.loads(response)

        if not data:
            raise UnavailableException(f"No data for {uuid}")

        manifest_urls = data.get('manifestUrls') or {}
        manifest_url = None
        subtitle_url = None
        stream_type = None

        # Manifest URLs (DASH or HLS)
        if 'dash' in manifest_urls:
            stream_type = STREAM_DASH
            manifest_url = manifest_urls['dash']
        elif 'hls' in manifest_urls:
            stream_type = STREAM_HLS
            manifest_url = manifest_urls['hls']

        # SSAI fallback
        elif data.get('adType') == 'SSAI' and data.get('ssai'):
            ssai = data['ssai']
            ssai_url = (
                f'https://pubads.g.doubleclick.net/ondemand/dash/content/'
                f'{ssai.get("contentSourceID")}/vid/{ssai.get("videoID")}/streams'
            )
            ad_data = json.loads(utils.post_url(ssai_url, data=''))
            manifest_url = ad_data.get('stream_manifest')
            subtitle_url = self.adjust_subtitle(ad_data)
            stream_type = STREAM_DASH

        if not manifest_url or not stream_type:
            raise UnavailableException(f"No valid manifest found for {uuid}")

        # DRM setup
        license_headers = None
        license_keys = None
        if drm_xml := data.get('drmXml'):
            license_headers = {'customdata': drm_xml}

            if (
                kodiutils.get_setting_bool('enable_widevine_device')
                and (device_path := kodiutils.get_setting('widevine_device'))
            ):
                # Widevine device-based DRM setup
                pssh_box = get_pssh_box(manifest_url)
                license_keys = get_license_keys(
                    self.LICENSE_URL,
                    license_headers,
                    pssh_box,
                    device_path,
                )

        return ResolvedStream(
            uuid=uuid,
            url=manifest_url,
            stream_type=stream_type,
            license_url=self.LICENSE_URL,
            license_headers=license_headers,
            license_keys=license_keys,
            subtitles=[subtitle_url] if subtitle_url else [],
        )

    def adjust_subtitle(self, ad_json):
        """Adjust subtitle"""
        subtitle_url = self.extract_subtitle_from_manifest(ad_json.get('stream_manifest'))
        subtitle = utils.get_url(subtitle_url)

        # Clean up old subtitles
        subtitle_dir = os.path.join(kodiutils.addon_profile(), 'subs', '')
        _, files = kodiutils.listdir(subtitle_dir)
        if files:
            for item in files:
                kodiutils.delete(os.path.join(subtitle_dir, item))

        # Cache original
        subtitle_path = os.path.join(subtitle_dir, 'T888.Original.Dutch.vtt')
        if not kodiutils.exists(subtitle_dir):
            kodiutils.mkdirs(subtitle_dir)
        with kodiutils.open_file(subtitle_path, 'w') as webvtt_output:
            webvtt_output.write(subtitle)

        time_events_url = ad_json.get('time_events_url')
        data = utils.get_url(time_events_url)

        events_json = json.loads(data)
        cues = events_json.get('cuepoints')

        ad_breaks = []
        webvtt_timing_regex = re.compile(r'\n(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\s')

        for cue in cues:
            duration = float(cue.get('end_float')) - float(cue.get('start_float'))
            ad_breaks.append({
                'start': cue.get('start_float'),
                'duration': duration
            })

        subtitle = webvtt_timing_regex.sub(lambda match: self.adjust_webvtt_timing(match, ad_breaks), subtitle)

        # Cache adjusted subtitles
        subtitle_path = os.path.join(subtitle_dir, 'T888.Dutch.vtt')
        with kodiutils.open_file(subtitle_path, 'w') as webvtt_output:
            webvtt_output.write(subtitle)
        return subtitle_path

    def adjust_webvtt_timing(self, match, ad_breaks):
        """Adjust the timing of a webvtt timestamp"""
        sub_timings = []
        for timestamp in match.groups():
            hours, minutes, seconds, millis = (int(x) for x in [timestamp[:-10], timestamp[-9:-7], timestamp[-6:-4], timestamp[-3:]])
            sub_timings.append(timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=millis))
        original_start_time = sub_timings[0]
        for ad_break in ad_breaks:
            # time format: seconds.fraction or seconds
            ad_break_start = timedelta(milliseconds=ad_break.get('start') * 1000)
            ad_break_duration = timedelta(milliseconds=ad_break.get('duration') * 1000)
            if ad_break_start <= original_start_time:
                # advance start and end timestamp
                for idx, item in enumerate(sub_timings):
                    sub_timings[idx] -= ad_break_duration
        for idx, item in enumerate(sub_timings):
            hours, remainder = divmod(item.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            millis = item.microseconds // 1000
            sub_timings[idx] = '%02d:%02d:%02d.%03d' % (hours, minutes, seconds, millis)
        adjusted_webvtt_timing = '\n{} --> {} '.format(sub_timings[0], sub_timings[1])
        return adjusted_webvtt_timing

    def extract_subtitle_from_manifest(self, manifest_url):
        """Extract subtitle URL from a DASH manifest"""
        from xml.etree.ElementTree import fromstring

        manifest_data = utils.get_url(manifest_url)
        manifest = fromstring(manifest_data)

        ns = {'mpd': 'urn:mpeg:dash:schema:mpd:2011'}

        base_url_el = manifest.find('mpd:BaseURL', ns)
        if base_url_el is None or not base_url_el.text:
            return None

        base_url = base_url_el.text

        for adaption in manifest.iterfind(
            './/mpd:AdaptationSet[@contentType="text"]', ns
        ):
            rep = adaption.find('mpd:Representation', ns)
            if rep is None:
                continue

            sub_base = rep.find('mpd:BaseURL', ns)
            if sub_base is None or not sub_base.text:
                continue

            sub_path = sub_base.text
            if 'T888' not in sub_path:
                continue

            # Strip period-specific suffix safely
            name, _, ext = sub_path.rpartition('.')
            clean_path = name.rsplit('_', 1)[0] + '.' + ext

            return base_url + clean_path

        return None

    def get_program_tree(self):
        """ Get a content tree with information about all the programs.
        :rtype list[Program]
        """
        page = 'programs'
        swimlanes = self.get_page(page)
        cards = []
        # get lanes
        for lane in swimlanes:
            index = lane.index
            # get lane by index
            _, data = self.get_swimlane(page, index)
            cards.extend(data)
        return cards

    def get_categories(self):
        """ Return a list of categories.
        :rtype list[Category]
        """
        content_tree = self.get_program_tree()
        categories = []
        cat_set = set()
        for item in content_tree:
            cat_obj = Category(uuid=item.category_id, title=item.category_name)
            if item.category_id not in cat_set:
                categories.append(cat_obj)
                cat_set.add(item.category_id)
        return categories

    def get_page(self, page, cache=CACHE_AUTO):
        """ Get a list of all swimlanes on a page.
        :rtype list[Swimlane]
        """

        def update():
            """ Fetch the pages metadata """
            data = utils.get_url(self.API_PLAY + '/tv/v2/pages/%s' % page, authentication='Bearer %s' % self._auth.get_token())
            result = json.loads(data)
            return result

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['pages', page], cache_mode=cache, update=update)
        if not data:
            return None

        swimlanes = []
        for item in data.get('lanes'):
            swimlanes.append(
                Swimlane(index=item.get('index'),
                         title=item.get('title'),
                         lane_type=item.get('laneType')
                )
            )
        return swimlanes

    def get_swimlane(self, page, index, limit=100, offset=0, cache=CACHE_PREVENT):
        """ Get a list of all categories.
        :rtype list[Episode], list[Program]
        """

        def update():
            """ Fetch the swimlane metadata """
            cards = []
            got_everything = False
            offset = 0
            while not got_everything:
                data = utils.get_url(self.API_PLAY + '/tv/v2/pages/%s/lanes/%s?limit=%s&offset=%s' % (page, index, limit, offset), authentication='Bearer %s' % self._auth.get_token())
                result = json.loads(data)
                cards.extend(result.get('cards'))
                total = result.get('total')
                if offset < (total - limit):
                    offset += limit
                else:
                    got_everything = True
            return cards

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['swimlane', page, index, limit, offset], cache_mode=cache, update=update)

        videos, programs = self._parse_cards_data(data)

        return videos, programs

    def search(self, query, limit=100, offset=0, cache=CACHE_AUTO):
        """ Search by query """
        def update():
            """ Fetch the search metadata """
            offset = 0
            payload = {
                'limit': limit,
                'offset': offset,
                'query': query,
            }
            cards = []
            got_everything = False
            while not got_everything:
                data = utils.post_url(self.API_PLAY + '/tv/v1/search', data=payload, authentication='Bearer %s' % self._auth.get_token())
                result = json.loads(data)
                cards.extend(result.get('cards'))
                total = result.get('total')
                if offset < (total - limit):
                    offset += limit
                else:
                    got_everything = True
            return cards

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['search', query, limit, offset], cache_mode=cache, update=update)

        videos, programs = self._parse_cards_data(data)
        return videos, programs

    def get_mylist(self):
        """ Get the content of My List
        :rtype list[Program]
        """
        data = utils.get_url(
            self.API_PLAY + '/tv/v1/programs/myList',
            authentication='Bearer %s' % self._auth.get_token()
        )
        result = json.loads(data)

        items = []
        for item in result:
            try:
                program = self.get_program(item)
                if program:
                    program.my_list = True
                    items.append(program)
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.warning(exc)

        return items

    def mylist_add(self, program_id):
        """ Add a program on My List """
        utils.put_url(
            self.API_PLAY + '/tv/v1/programs/%s/myList' % program_id,
            data={'onMyList': True},
            authentication='Bearer %s' % self._auth.get_token()
        )

    def mylist_del(self, program_id):
        """ Remove a program on My List """
        utils.put_url(
            self.API_PLAY + '/tv/v1/programs/%s/myList' % program_id,
            data={'onMyList': False},
            authentication='Bearer %s' % self._auth.get_token()
        )

    def update_position(self, video_id, position):
        """ Update resume position of a video """
        utils.put_url(
            self.API_PLAY + '/tv/v1/videos/%s/position' % video_id,
            data={'position': position},
            authentication='Bearer %s' % self._auth.get_token()
        )

    def delete_position(self, video_id):
        """ Update resume position of a video """
        utils.delete_url(
            self.API_PLAY + '/web/v1/videos/continue-watching/%s' % video_id,
            authentication='Bearer %s' % self._auth.get_token()
        )

    @staticmethod
    def _parse_program_data(data):
        """ Parse the Program JSON.
        :type data: dict
        :rtype Program
        """
        # Create Program info
        program = Program(
            uuid=data.get('programUuid'),
            path=data.get('programUuid'),
            channel=data.get('brand'),
            category_name=data.get('category') or 'No category',
            title=data.get('title'),
            description=html_to_kodi(data.get('description')),
            aired=datetime.fromtimestamp(data.get('dates', {}).get('publishDate', 0.0) or 0.0),
            expiry=datetime.fromtimestamp(data.get('dates', {}).get('unpublishDate', 0.0) or 0.0),
            poster=data.get('images').get('portrait'),
            thumb=data.get('images').get('portrait'),
            fanart=data.get('images').get('background'),
        )

        # Create Season info

        program.seasons = {
            key: Season(
                uuid=playlist.get('playlistUuid'),
                title=playlist.get('title'),
                number=re.compile(r'\d+$').findall(playlist.get('title'))[-1] if re.compile(r'\d+$').findall(playlist.get('title')) else None,
            )
            for key, playlist in enumerate(data.get('playlists', [])) if playlist.get('title')
        }

        return program


    @staticmethod
    def _parse_cards_data(data):
        """ Parse the Cards JSON.
        :type data: dict
        ::rtype list[Episode], list[Program]
        """
        videos = []
        programs = []
        for card in data:
            if card.get('type') == 'PROGRAM':
                # Program
                programs.append(Program(
                    uuid=card.get('uuid'),
                    title=card.get('title'),
                    category_id=str(card.get('categoryId')),
                    category_name=card.get('category') or 'No category',
                    poster=card.get('images')[0].get('url'),
                    channel=card.get('brand'),
                ))
            elif card.get('type') == 'VIDEO':
                # Video
                videos.append(Episode(
                    uuid=card.get('uuid'),
                    title=card.get('subtitle'),
                    channel=card.get('brand'),
                    description=html_to_kodi(card.get('description')),
                    duration=card.get('duration'),
                    position=card.get('position'),
                    thumb=card.get('images')[0].get('url'),
                    program_title=card.get('title'),
                    aired=datetime.fromtimestamp(card.get('dates', {}).get('publishDate', 0.0) or 0.0),
                    expiry=datetime.fromtimestamp(card.get('dates', {}).get('unpublishDate', 0.0) or 0.0),
                    content_type='long_form',
                ))
        return videos, programs


    @staticmethod
    def _parse_playlist_data(data):
        """ Parse the Playlist JSON.
        :type data: dict
        :rtype Playlist
        """
        # Create Playlist info
        playlist = [
            Episode(
                uuid=video.get('videoUuid'),
                title=video.get('title'),
                aired=datetime.fromtimestamp(video.get('dates', {}).get('publishDate', 0.0) or 0.0),
                expiry=datetime.fromtimestamp(video.get('dates', {}).get('unpublishDate', 0.0) or 0.0),
                description=html_to_kodi(video.get('description')),
                thumb=video.get('image'),
                duration=video.get('duration'),
                #number=video.get('title').split()[1],
                content_type='long_form',
            )
            for video in data.get('videos', [])
        ]
        return playlist


    @staticmethod
    def _parse_channels_data(data):
        """ Parse the Channel JSON.
        :type data: dict
        :rtype list[Channel]
        """
        # Create Channel info
        channels = [
            Channel(
                uuid=channel.get('uuid'),
                index=channel.get('index'),
                title=channel.get('title'),
                description=html_to_kodi(channel.get('description')),
                brand=channel.get('brand'),
                logo=channel.get('transparentLogo')[0].get('url'),
                fanart=channel.get('images')[2].get('url'),
            )
            for channel in data
        ]
        return channels


    @staticmethod
    def _parse_episode_data(data, season_uuid=None):
        """ Parse the Episode JSON.
        :type data: dict
        :type season_uuid: str
        :rtype Episode
        """
        if data.get('episodeNumber'):
            episode_number = data.get('episodeNumber')
        else:
            # The episodeNumber can be absent
            match = re.compile(r'\d+$').search(data.get('title'))
            if match:
                episode_number = match.group(0)
            else:
                episode_number = None

        episode = Episode(
            uuid=data.get('videoUuid'),
            nodeid=data.get('pageInfo', {}).get('nodeId'),
            path=data.get('link').lstrip('/'),
            channel=data.get('pageInfo', {}).get('site'),
            program_title=data.get('program', {}).get('title') if data.get('program') else data.get('title'),
            title=data.get('title'),
            description=html_to_kodi(data.get('description')),
            thumb=data.get('image'),
            duration=data.get('duration'),
            season=data.get('seasonNumber'),
            season_uuid=season_uuid,
            number=episode_number,
            aired=datetime.fromtimestamp(int(data.get('createdDate'))),
            expiry=datetime.fromtimestamp(int(data.get('unpublishDate'))) if data.get('unpublishDate') else None,
            rating=data.get('parentalRating'),
            stream=data.get('path'),
            content_type=data.get('type'),
        )
        return episode

    @staticmethod
    def _parse_clip_data(data):
        """ Parse the Clip JSON.
        :type data: dict
        :rtype Episode
        """
        episode = Episode(
            uuid=data.get('videoUuid'),
            program_title=data.get('title'),
            title=data.get('title'),
        )
        return episode

    def _handle_cache(self, key, cache_mode, update, ttl=30 * 24 * 60 * 60):
        """ Fetch something from the cache, and update if needed """
        if cache_mode in [CACHE_AUTO, CACHE_ONLY]:
            # Try to fetch from cache
            data = self._get_cache(key)
            if data is None and cache_mode == CACHE_ONLY:
                return None
        else:
            data = None

        if data is None:
            try:
                # Fetch fresh data
                _LOGGER.debug('Fetching fresh data for key %s', '.'.join(str(x) for x in key))
                data = update()
                if data:
                    # Store fresh response in cache
                    self._set_cache(key, data, ttl)
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.warning('Something went wrong when refreshing live data: %s. Using expired cached values.', exc)
                data = self._get_cache(key, allow_expired=True)

        return data

    def _get_cache(self, key, allow_expired=False):
        """ Get an item from the cache """
        filename = ('.'.join(str(x) for x in key) + '.json').replace('/', '_')
        fullpath = os.path.join(self._cache_path, filename)

        if not os.path.exists(fullpath):
            return None

        if not allow_expired and os.stat(fullpath).st_mtime < time.time():
            return None

        with open(fullpath, 'r', encoding='utf-8') as fdesc:
            try:
                _LOGGER.debug('Fetching %s from cache', filename)
                value = json.load(fdesc)
                return value
            except (ValueError, TypeError):
                return None

    def _set_cache(self, key, data, ttl):
        """ Store an item in the cache """
        filename = ('.'.join(str(x) for x in key) + '.json').replace('/', '_')
        fullpath = os.path.join(self._cache_path, filename)

        if not os.path.exists(self._cache_path):
            os.makedirs(self._cache_path)

        with open(fullpath, 'w', encoding='utf-8') as fdesc:
            _LOGGER.debug('Storing to cache as %s', filename)
            json.dump(data, fdesc)

        # Set TTL by modifying modification date
        deadline = int(time.time()) + ttl
        os.utime(fullpath, (deadline, deadline))
