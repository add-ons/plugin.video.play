# -*- coding: utf-8 -*-
""" Tests for Content API """

import logging
import os
import unittest

from resources.lib import kodiutils
from resources.lib.play import ResolvedStream
from resources.lib.play.auth import AuthApi
from resources.lib.play.content import ContentApi, GeoblockedException, Program, CACHE_PREVENT, Category

_LOGGER = logging.getLogger(__name__)


class TestApi(unittest.TestCase):
    """ Tests for Content Api """
    def __init__(self, *args, **kwargs):
        super(TestApi, self).__init__(*args, **kwargs)
        auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(auth, cache_path=kodiutils.get_cache_path())

    def test_programs(self):
        """ Test getting programs"""
        programs = self._api.get_programs()
        self.assertIsInstance(programs, list)
        self.assertIsInstance(programs[0], Program)

    def test_recommendations(self):
        """ Test getting recommendation categories """
        categories = self._api.get_categories()
        self.assertIsInstance(categories, list)

    def test_categories(self):
        """ Test getting categories """
        categories = self._api.get_categories()
        self.assertIsInstance(categories, list)
        self.assertIsInstance(categories[0], Category)

        programs = self._api.get_programs(category=categories[0].uuid)
        self.assertIsInstance(programs, list)
        self.assertIsInstance(programs[0], Program)

    def test_episodes(self):
        """ Test getting program season episodes """
        for program in ['20cdf366-f7ac-4bf8-995a-2af53c89655d', '2e0768da-29b0-4945-821b-f76395f26876']: # Nonkels, Kiekenkotkwis
            program = self._api.get_program(program, cache=CACHE_PREVENT)
            self.assertIsInstance(program, Program)
            self.assertIsInstance(program.seasons, dict)

    @unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
    def test_get_stream(self):
        """ Test getting resolved stream """
        try:
            program = self._api.get_program('20cdf366-f7ac-4bf8-995a-2af53c89655d') # Nonkels
            self.assertIsInstance(program, Program)
            episode = self._api.get_episodes(program.seasons[0].uuid)[0]
            resolved_stream = self._api.get_stream(episode.uuid, episode.content_type)
            self.assertIsInstance(resolved_stream, ResolvedStream)
        except GeoblockedException as ex:
            _LOGGER.error(ex)

    @unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
    @unittest.skipIf(os.getenv('GITHUB_ACTIONS') == 'true', 'Skipping on GitHub Actions')
    def test_get_drm_stream(self):
        """ Test getting DRM protected resolved stream """
        try:
            program = self._api.get_program('9c33ef37-6112-49a1-8262-fdc4e8c2266f') # NCIS
            self.assertIsInstance(program, Program)
            episode = self._api.get_episodes(program.seasons[0].uuid)[0]
            resolved_stream = self._api.get_stream(episode.uuid, episode.content_type)
            self.assertIsInstance(resolved_stream, ResolvedStream)
        except GeoblockedException as ex:
            _LOGGER.error(ex)

    @unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
    def test_get_mylist(self):
        """ Test getting favorite programs list """
        my_list =  self._api.get_mylist()
        self.assertIsInstance(my_list, list)
        if len(my_list) > 0:
            self.assertIsInstance(my_list[0], Program)

    @unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
    def test_mylist_add(self):
        """ Test adding a program to favorite programs list """
        self._api.mylist_add('706542fa-dec9-4675-9b7c-b317720e8bd0')  # Callboys

    @unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
    def test_mylist_del(self):
        """ Test removing a program from favorite programs list """
        self._api.mylist_del('706542fa-dec9-4675-9b7c-b317720e8bd0')  # Callboys

    def test_search(self):
        """ Test searching for a program """
        _, programs = self._api.search('de mol')
        self.assertIsInstance(programs, list)
        self.assertIsInstance(programs[0], Program)

    def test_search_empty(self):
        """ Test searching with empty query """
        _, programs = self._api.search('')
        self.assertIsInstance(programs, list)

    def test_search_space(self):
        """ Test searching with space query """
        _, programs = self._api.search(' ')
        self.assertIsInstance(programs, list)


if __name__ == '__main__':
    unittest.main()
