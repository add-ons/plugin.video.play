# -*- coding: utf-8 -*-
""" Tests for AUTH API """

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.play.auth import AuthApi

_LOGGER = logging.getLogger(__name__)


class TestAuth(unittest.TestCase):
    """Tests for authentication """
    def __init__(self, *args, **kwargs):
        super(TestAuth, self).__init__(*args, **kwargs)

    @unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
    def test_login(self):
        """ Test login procedure """
        auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())

        # Clear any cache we have
        auth.clear_tokens()

        # We should get a token by logging in
        id_token = auth.get_token()
        self.assertTrue(id_token)

        # Test it a second time, it should go from memory now
        id_token = auth.get_token()
        self.assertTrue(id_token)


if __name__ == '__main__':
    unittest.main()
