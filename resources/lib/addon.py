# -*- coding: utf-8 -*-
""" Addon code """

import logging

from routing import Plugin

from resources.lib import kodilogging

routing = Plugin()  # pylint: disable=invalid-name
_LOGGER = logging.getLogger(__name__)


@routing.route('/')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu().show_mainmenu()


@routing.route('/channels')
def show_channels():
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channels()


@routing.route('/channels/<uuid>')
def show_channel_menu(uuid):
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_menu(uuid)


@routing.route('/channels/<channel>/catalog')
def show_channel_catalog(channel):
    """ Show the catalog of a channel """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_catalog_channel(channel)


@routing.route('/catalog')
def show_catalog():
    """ Show the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_catalog()


@routing.route('/catalog/<uuid>')
def show_catalog_program(uuid):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program(uuid)


@routing.route('/catalog/season/<uuid>')
def show_catalog_program_season(uuid):
    """ Show a season from a program """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_season(uuid)


@routing.route('/category')
def show_categories():
    """ Show the catalog by category """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_categories()


@routing.route('/category/<category>')
def show_category(category):
    """ Show the catalog by category """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_category(category)


@routing.route('/recommendations')
def show_recommendations():
    """ Show my list """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_recommendations()


@routing.route('/recommendations/<category>')
def show_recommendations_category(category):
    """ Show my list """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_recommendations_category(category)


@routing.route('/mylist')
def show_mylist():
    """ Show my list """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_mylist()


@routing.route('/mylist/add/<uuid>/<title>')
def mylist_add(uuid, title):
    """ Add a program to My List """
    from resources.lib.modules.catalog import Catalog
    Catalog().mylist_add(uuid, title)


@routing.route('/mylist/del/<uuid>/<title>')
def mylist_del(uuid, title):
    """ Remove a program from My List """
    from resources.lib.modules.catalog import Catalog
    Catalog().mylist_del(uuid, title)


@routing.route('/continue')
def continue_watching():
    """ Show continue watching list """
    from resources.lib.modules.catalog import Catalog
    Catalog().continue_watching()


@routing.route('/search')
@routing.route('/search/<query>')
def show_search(query=None):
    """ Shows the search dialog """
    from resources.lib.modules.search import Search
    Search().show_search(query)


@routing.route('/play/catalog')
@routing.route('/play/catalog/<uuid>')
@routing.route('/play/catalog/<uuid>/<content_type>')
def play_catalog(uuid=None, content_type='video'):
    """ Play the requested item """
    from resources.lib.modules.player import Player
    Player().play(uuid, content_type)


@routing.route('/channels/<channel>/tvguide')
def show_channel_tvguide(channel):
    """ Shows the dates in the tv guide """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide().show_channel(channel)


@routing.route('/channels/<channel>/tvguide/<date>')
def show_channel_tvguide_detail(channel=None, date=None):
    """ Shows the programs of a specific date in the tv guide """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide().show_detail(channel, date)


@routing.route('/iptv/channels')
def iptv_channels():
    """ Generate channel data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IPTVManager
    IPTVManager(int(routing.args['port'][0])).send_channels()  # pylint: disable=too-many-function-args


@routing.route('/iptv/epg')
def iptv_epg():
    """ Generate EPG data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IPTVManager
    IPTVManager(int(routing.args['port'][0])).send_epg()  # pylint: disable=too-many-function-args

@routing.route('/cache/clear')
def clear_cache():
    """ Clear the cache """
    from resources.lib.modules.catalog import Catalog
    Catalog().clear_cache()


def run(params):
    """ Run the routing plugin """
    kodilogging.config()
    routing.run(params)
