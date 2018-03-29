# -*- coding: utf-8 -*-
#
#  Copyright 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Tests block operations."""

from rsa._compat import b

try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import unittest

import rsa
from rsa import bigfile, varblock, pkcs1


class BigfileTest(unittest.TestCase):
    def test_encrypt_decrypt_bigfile(self):
        # Expected block size + 11 bytes padding
        pub_key, priv_key = rsa.newkeys((6 + 11) * 8)

        # Encrypt the file
        message = b('123456Sybren')
        infile = BytesIO(message)
        outfile = BytesIO()

        bigfile.encrypt_bigfile(infile, outfile, pub_key)

        # Test
        crypto = outfile.getvalue()

        cryptfile = BytesIO(crypto)
        clearfile = BytesIO()

        bigfile.decrypt_bigfile(cryptfile, clearfile, priv_key)
        self.assertEquals(clearfile.getvalue(), message)

        # We have 2x6 bytes in the message, so that should result in two
        # bigfile.
        cryptfile.seek(0)
        varblocks = list(varblock.yield_varblocks(cryptfile))
        self.assertEqual(2, len(varblocks))

    def test_sign_verify_bigfile(self):
        # Large enough to store MD5-sum and ASN.1 code for MD5
        pub_key, priv_key = rsa.newkeys((34 + 11) * 8)

        # Sign the file
        msgfile = BytesIO(b('123456Sybren'))
        signature = pkcs1.sign(msgfile, priv_key, 'MD5')

        # Check the signature
        msgfile.seek(0)
        self.assertTrue(pkcs1.verify(msgfile, signature, pub_key))

        # Alter the message, re-check
        msgfile = BytesIO(b('123456sybren'))
        self.assertRaises(pkcs1.VerificationError,
                          pkcs1.verify, msgfile, signature, pub_key)
