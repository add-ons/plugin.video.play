# -*- coding: utf-8 -*-
""" EPG API """

import re
import json
import logging
from datetime import datetime, timedelta

import dateutil.parser
import dateutil.tz
import requests

from resources.lib import kodiutils

_LOGGER = logging.getLogger(__name__)

GENRE_MAPPING = {
    'Detective': 0x11,
    'Dramaserie': 0x15,
    'Fantasy': 0x13,
    'Human Interest': 0x00,
    'Informatief': 0x20,
    'Komedie': 0x14,
    'Komische serie': 0x14,
    'Kookprogramma': '',
    'Misdaadserie': 0x15,
    'Politieserie': 0x17,
    'Reality': 0x31,
    'Science Fiction': 0x13,
    'Show': 0x30,
    'Thriller': 0x11,
    'Voetbal': 0x43,
}

PROXIES = kodiutils.get_proxies()


class EpgProgram:
    """ Defines a Program in the EPG. """

    # pylint: disable=invalid-name
    def __init__(self, channel, program_title, episode_title, episode_title_original, number, season, genre, start,
                 won_id, won_program_id, program_description, description, duration, program_url, video_url, thumb,
                 airing):
        self.channel = channel
        self.program_title = program_title
        self.episode_title = episode_title
        self.episode_title_original = episode_title_original
        self.number = number
        self.season = season
        self.genre = genre
        self.start = start
        self.won_id = won_id
        self.won_program_id = won_program_id
        self.program_description = program_description
        self.description = description
        self.duration = duration
        self.program_url = program_url
        self.video_url = video_url
        self.thumb = thumb
        self.airing = airing

        if GENRE_MAPPING.get(self.genre):
            self.genre_id = GENRE_MAPPING.get(self.genre)
        else:
            self.genre_id = None

    def __repr__(self):
        return "%r" % self.__dict__


class EpgApi:
    """ GoPlay EPG API """

    EPG_ENDPOINTS = {
        # 'Play4': 'https://www.goplay.be/api/epg/vier/{date}',
        'Play 4': 'https://www.play.tv/tv-gids/play/{date}',
        'Play 5': 'https://www.play.tv/tv-gids/fictie/{date}',
        'Play 6': 'https://www.play.tv/tv-gids/actie/{date}',
        'Play 7': 'https://www.play.tv/tv-gids/reality/{date}',
        'Play Crime': 'https://www.play.tv/tv-gids/crime/{date}'
    }

    EPG_NO_BROADCAST = 'Geen uitzending'

    def __init__(self):
        """ Initialise object """
        self._session = requests.session()

    def get_epg(self, channel, date):
        """ Returns the EPG for the specified channel and date.
        :type channel: str
        :type date: str
        :rtype list[EpgProgram]
        """
        #_LOGGER.info("Getting info for channel %s on date %s", channel, date)
        if channel not in self.EPG_ENDPOINTS:
            raise Exception('Unknown channel %s' % channel)

        if date is None:
            # Fetch today when no date is specified
            date = datetime.today().strftime('%Y-%m-%d')
        elif date == 'yesterday':
            date = (datetime.today() + timedelta(days=-1)).strftime('%Y-%m-%d')
        elif date == 'today':
            date = datetime.today().strftime('%Y-%m-%d')
        elif date == 'tomorrow':
            date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

        try:
            response = self._get_url(self.EPG_ENDPOINTS.get(channel).format(date=date))
            _LOGGER.info(f"Date is {date} and channel is {channel}")
            pattern = r'\\"id\\":\\"tvguide-list\\",\\"children\\":(.*?\]\)<\/script><\/body><\/html>)'
            stresult = re.search(pattern,response)
            stresult=stresult.group(1)
            stresult=stresult.replace(r'\\\"',r'\\\'')
            stresult=stresult.replace('\\','')
            pattern = r'\"children\":(.*?\]\))<\/script><\/body><\/html>'
            resp = re.search(pattern,stresult)
            resp = resp.group(1)
            pattern = r'}],("\$L.*?\])'
            nextjs = re.search(pattern,resp)
            respnjs='[' + nextjs.group(1)
            lst = json.loads(respnjs)
            nextst = ''
            for i, val in enumerate(lst):   # some elements are missing: missing $
                ref=lst[i].replace('$L','')
                psstr=r'<script>self\.__next_f\.push\(\[1,"' + ref + r':(\["\$".*?}])'
                match = re.search(psstr, resp)
                if match:
                    respnjs = match.group(1)
                    nextst += ',' + respnjs
                else:
                    _LOGGER.warning(f"No match found for reference: {ref}")
            pattern = r'\"children\":(.*?}]),\"\$L'   # r'\"children\":(.*?\"}}],)\"\$L'"
            resp = re.search(pattern,stresult)
            resp = resp.group(1) + nextst + "]"
            data = json.loads(resp)
            return [self._parse_program(channel, x) for x in data if self.EPG_NO_BROADCAST not in x[3]['program']['programTitle']]
        except Exception as e:  # pylint: disable=broad-exception-caught
            ptitle = f"Error occured : {e}"
            _LOGGER.info("Date is %s and channel is %s, %s", date, channel, ptitle)
            date_ymd = date.split("-")
            ts = self.convert_to_timestamp(date_ymd[0], date_ymd[1], date_ymd[2]) + 28800
            y=['$', '$L31', '', {'program': {'classification': {'age': 12, 'icons': {'summary': [], 'full': ['violence', 'fear', 'badLanguage']}}, 'contentEpisode': 'Error', 'dateString': date, 'duration': 43200, 'episodeNr': '1', 'episodeTitle': 'Error', 'genre': 'Actie', 'isMovie': False, 'latestVideo': False, 'originalTitle': None, 'program': None, 'programConcept': 'Actieserie', 'programTitle': ptitle, 'season': '1', 'timeString': '08:00', 'timestamp': ts, 'video': None, 'wonId': None, 'wonProgramId': None}}]
            return [self._parse_program(channel, y)]

    @staticmethod
    def _parse_program(channel, data):
        """ Parse the EPG JSON data to a EpgProgram object.
        :type channel: str
        :type data: dict
        :rtype EpgProgram
        """
        duration = int(data[3]['program']['duration']) if data[3]['program']['duration'] else None
        # Check if this broadcast is currently airing
        timestamp = datetime.now().replace(tzinfo=dateutil.tz.gettz('CET'))
        start = datetime.fromtimestamp(data[3]['program']['timestamp']).replace(tzinfo=dateutil.tz.gettz('CET'))
        if duration:
            airing = bool(start <= timestamp < (start + timedelta(seconds=duration)))
        else:
            airing = False

        # Only allow direct playing if the linked video is the actual program
        if data[3]['program']['video']:
            video_url = data[3]['program']['video']['uuid']
            thumb = data[3]['program']['video']['data']['images']['default']
        else:
            video_url = None
            thumb = None

        epg_program = EpgProgram(
            channel=channel,
            program_title=data[3]['program']['programTitle'],
            episode_title=data[3]['program']['episodeTitle'],
            episode_title_original=data[3]['program']['originalTitle'],
            number=int(data[3]['program']['episodeNr']) if data[3]['program']['episodeNr'] else None,
            season=data[3]['program']['season'],
            genre=data[3]['program']['genre'],
            start=start,
            won_id=int(data[3]['program']['wonId']) if data[3]['program']['wonId'] else None,
            won_program_id=int(data[3]['program']['wonProgramId']) if data[3]['program']['wonProgramId'] else None,
            program_description=data[3]['program']['programConcept'],
            description=data[3]['program']['contentEpisode'],
            duration=duration,
            program_url=data[3]['program']['program']['uuid'] if data[3]['program']['program'] else None,
            video_url=video_url,
            thumb=thumb,
            airing=airing,
        )
        return epg_program

    def get_broadcast(self, channel, timestamp):
        """ Load EPG information for the specified channel and date.
        :type channel: str
        :type timestamp: str
        :rtype: EpgProgram
        """
        # Parse to a real datetime
        timestamp = dateutil.parser.parse(timestamp).replace(tzinfo=dateutil.tz.gettz('CET'))

        # Load guide info for this date
        programs = self.get_epg(channel=channel, date=timestamp.strftime('%Y-%m-%d'))

        # Find a matching broadcast
        for broadcast in programs:
            if broadcast.start <= timestamp < (broadcast.start + timedelta(seconds=broadcast.duration)):
                return broadcast

        return None

    def _get_url(self, url):
        """ Makes a GET request for the specified URL.
        :type url: str
        :rtype str
        """
        response = self._session.get(url, proxies=PROXIES)

        if response.status_code != 200:
            raise Exception('Could not fetch data')

        return response.text

    def is_leap_year(self, year):
        """ Checks if a year is a leap year """
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


    def convert_to_timestamp(self, year, month, day):
        """ Converts year, month, and day to Linux timestamp without datetime lib """
        year=int(year)
        month=int(month)
        day=int(day)

        # Days in each month for regular and leap years
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        # Account for leap year
        if self.is_leap_year(year):
            days_in_month[1] = 29

        # Seconds in a day
        seconds_per_day = 86400

        # Calculate the total number of days since Unix epoch (1970-01-01)
        total_days = 0

        # Add days for each year since 1970
        for y in range(1970, year):
            total_days += 366 if self.is_leap_year(y) else 365

        # Add days for each month in the given year
        for m in range(1, month):
            total_days += days_in_month[m - 1]

        # Add the days in the given month
        total_days += day - 1  # Subtract 1 because the epoch starts at the beginning of the day

        # Convert days to seconds
        return total_days * seconds_per_day
