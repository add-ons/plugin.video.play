# -*- coding: utf-8 -*-
""" Tests for Routing """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from resources.lib import addon


routing = addon.routing  # pylint: disable=invalid-name


class TestRouting(unittest.TestCase):
    """ Tests for Routing """

    def __init__(self, *args, **kwargs):
        super(TestRouting, self).__init__(*args, **kwargs)

    def setUp(self):
        # Don't warn that we don't close our HTTPS connections, this is on purpose.
        # warnings.simplefilter("ignore", ResourceWarning)
        pass

    def test_main_menu(self):
        routing.run([routing.url_for(addon.show_main_menu), '0', ''])

    def test_channels_menu(self):
        routing.run([routing.url_for(addon.show_channels), '0', ''])
        routing.run([routing.url_for(addon.show_channel_menu, uuid='26d776d2-7cff-4dd5-86e5-cdff9ab1f364'), '0', ''])  # Play 4

    def test_catalog_menu(self):
        routing.run([routing.url_for(addon.show_catalog), '0', ''])

    def test_recommendations_menu(self):
        routing.run([routing.url_for(addon.show_recommendations), '0', ''])

    def test_recommendations_category_menu(self):
        routing.run([routing.url_for(addon.show_recommendations_category, category='2'), '0', ''])  # 2 Net toegevoegd op Play

    def test_catalog_channel_menu(self):
        routing.run([routing.url_for(addon.show_channel_catalog, channel='Play4'), '0', ''])

    def test_catalog_program_menu(self):
        routing.run([routing.url_for(addon.show_catalog_program, uuid='7f9c4278-8372-47ef-9cc8-cc10c7b7c9f5'), '0', ''])  # De Mol

    def test_catalog_program_season_menu(self):
        routing.run([routing.url_for(addon.show_catalog_program_season, uuid='eeb790c9-1264-4eee-9209-d98627626988'), '0', ''])  # De Mol Seizoen 12

    def test_categories_menu(self):
        routing.run([routing.url_for(addon.show_categories), '0', ''])

    def test_category_menu(self):
        routing.run([routing.url_for(addon.show_category, category='5285'), '0', ''])  # 5285 Fictie

    def test_continue_watching_menu(self):
        routing.run([routing.url_for(addon.continue_watching), '0', ''])

    def test_search_menu(self):
        routing.run([routing.url_for(addon.show_search), '0', ''])
        routing.run([routing.url_for(addon.show_search, query='de mol'), '0', ''])


if __name__ == '__main__':
    unittest.main()
