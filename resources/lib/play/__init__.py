# -*- coding: utf-8 -*-
""" Play API """

STREAM_DICT = {
    'codec': 'h264',
    'height': 544,
    'width': 960,
}


class ResolvedStream:
    """ Defines a stream that we can play"""

    def __init__(self, uuid=None, url=None, stream_type=None, license_url=None, license_headers=None, license_keys=None):
        """
        :type uuid: str
        :type url: str
        :type stream_type: str
        :type license_url: str
        :type license_headers: str
        :type license_keys: dict
        """
        self.uuid = uuid
        self.url = url
        self.stream_type = stream_type
        self.license_url = license_url
        self.license_headers = license_headers
        self.license_keys = license_keys

    def __repr__(self):
        return "%r" % self.__dict__
