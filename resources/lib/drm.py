# -*- coding: utf-8 -*-
""" DRM UTILS """

from xml.etree.ElementTree import XML

from resources.lib.play import utils

class MissingModuleException(Exception):
    """ Is thrown when a Python module is missing. """


def get_pssh_box(manifest_url):
    """ Get PSSH Box.
    :type manifest_url: str
    :rtype str
    """
    pssh_box = None
    manifest_data = utils.get_url(manifest_url)
    manifest = XML(manifest_data)
    mpd_ns = {'mpd': 'urn:mpeg:dash:schema:mpd:2011'}
    cenc_ns = {'cenc': 'urn:mpeg:cenc:2013'}
    adaptionset = manifest.find('mpd:Period', mpd_ns).find('mpd:AdaptationSet', mpd_ns)
    pssh_box = adaptionset.findall('mpd:ContentProtection', mpd_ns)[1].find('cenc:pssh', cenc_ns).text
    return pssh_box


def get_license_keys(license_url, license_headers, pssh_box, device_path):
    """Get cenc license keys from Widevine CDM.
    :type license_url: str
    :type headers: str
    :type pssh_box: str
    :type device_path: str
    :rtype dict
    """
    try:
        from pywidevine.cdm import Cdm
        from pywidevine.device import Device
        from pywidevine.pssh import PSSH
    except ModuleNotFoundError as exc:
        raise MissingModuleException(exc)

    # Load device
    device = Device.load(device_path)

    # Load CDM
    cdm = Cdm.from_device(device)

    # Open cdm session
    session_id = cdm.open()

    # Get license challenge
    challenge = cdm.get_license_challenge(session_id, PSSH(pssh_box))

    # Request
    wv_license = utils.post_url(license_url, headers=license_headers, data=challenge)

    # parse license challenge
    cdm.parse_license(session_id, wv_license)

    # Get keys
    license_keys = {}
    for key in cdm.get_keys(session_id):
        if key.type == 'CONTENT':
            license_keys[key.kid.hex] = key.key.hex()

    # close session, disposes of session data
    cdm.close(session_id)

    return license_keys
