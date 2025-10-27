# -*- coding: utf-8 -*-
""" Exceptions """

class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class NoContentException(Exception):
    """ Is thrown when no items are unavailable. """


class GeoblockedException(Exception):
    """ Is thrown when a geoblocked item is played. """


class ApiException(Exception):
    """ Is thrown when the Api return an error. """
