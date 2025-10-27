# -*- coding: utf-8 -*-
""" UTILS """

import logging
import requests

from resources.lib import kodiutils
from resources.lib.play.exceptions import ApiException, GeoblockedException

_LOGGER = logging.getLogger(__name__)

SESSION = requests.session()
PROXIES = kodiutils.get_proxies()

@staticmethod
def handle_error_message(response):
    """ Returns the error message of an Api request.
    :type response: requests.Response Object
    """
    if response.json().get('message'):
        message = response.json().get('message')
    elif response.json().get('errormsg'):
        message = response.json().get('errormsg')
    else:
        message = response.text

    _LOGGER.error(message)
    if response.status_code == 451:
        raise GeoblockedException(message)
    raise ApiException(message)


def get_url(url, params=None, headers=None, authentication=None):
    """ Makes a GET request for the specified URL.
    :type url: str
    :type authentication: str
    :rtype str
    """
    try:
        if authentication:
            response = SESSION.get(url, params=params, headers={
                'authorization': authentication,
            }, proxies=PROXIES)
        else:
            response = SESSION.get(url, params=params, headers=headers, proxies=PROXIES)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        handle_error_message(response)

    return response.text


def post_url(url, params=None, headers=None, data=None, authentication=None):
    """ Makes a POST request for the specified URL.
    :type url: str
    :type authentication: str
    :rtype str
    """
    try:
        if authentication:
            response = SESSION.post(url, params=params, json=data, headers={
                'authorization': authentication,
            }, proxies=PROXIES)
        else:
            response = SESSION.post(url, params=params, headers=headers, data=data, proxies=PROXIES)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        handle_error_message(response)

    return response.content


def put_url(url, params=None, headers=None, data=None, authentication=None):
    """ Makes a PUT request for the specified URL.
    :type url: str
    :type authentication: str
    :rtype str
    """
    try:
        if authentication:
            response = SESSION.put(url, params=params, json=data, headers={
                'authorization': authentication,
            }, proxies=PROXIES)
        else:
            response = SESSION.put(url, params=params, headers=headers, json=data, proxies=PROXIES)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        handle_error_message(response)

    return response.text


def delete_url(url, params=None, headers=None, authentication=None):
    """ Makes a DELETE request for the specified URL.
    :type url: str
    :type authentication: str
    :rtype str
    """
    try:
        if authentication:
            response = SESSION.delete(url, params=params, headers={
                'authorization': authentication,
            }, proxies=PROXIES)
        else:
            response = SESSION.delete(url, params=params, headers=headers, proxies=PROXIES)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        handle_error_message(response)

    return response.text
