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

"""Tests PKCS #1 version 2 functionality.

Most of the mocked values come from the test vectors found at:
http://www.itomorrowmag.com/emc-plus/rsa-labs/standards-initiatives/pkcs-rsa-cryptography-standard.htm
"""

import unittest

from rsa import pkcs1_v2


class MGFTest(unittest.TestCase):
    def test_oaep_int_db_mask(self):
        seed = (
            b'\xaa\xfd\x12\xf6\x59\xca\xe6\x34\x89\xb4\x79\xe5\x07\x6d\xde\xc2'
            b'\xf0\x6c\xb5\x8f'
        )
        db = (
            b'\xda\x39\xa3\xee\x5e\x6b\x4b\x0d\x32\x55\xbf\xef\x95\x60\x18\x90'
            b'\xaf\xd8\x07\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xd4\x36\xe9\x95\x69'
            b'\xfd\x32\xa7\xc8\xa0\x5b\xbc\x90\xd3\x2c\x49'
        )
        masked_db = (
            b'\xdc\xd8\x7d\x5c\x68\xf1\xee\xa8\xf5\x52\x67\xc3\x1b\x2e\x8b\xb4'
            b'\x25\x1f\x84\xd7\xe0\xb2\xc0\x46\x26\xf5\xaf\xf9\x3e\xdc\xfb\x25'
            b'\xc9\xc2\xb3\xff\x8a\xe1\x0e\x83\x9a\x2d\xdb\x4c\xdc\xfe\x4f\xf4'
            b'\x77\x28\xb4\xa1\xb7\xc1\x36\x2b\xaa\xd2\x9a\xb4\x8d\x28\x69\xd5'
            b'\x02\x41\x21\x43\x58\x11\x59\x1b\xe3\x92\xf9\x82\xfb\x3e\x87\xd0'
            b'\x95\xae\xb4\x04\x48\xdb\x97\x2f\x3a\xc1\x4f\x7b\xc2\x75\x19\x52'
            b'\x81\xce\x32\xd2\xf1\xb7\x6d\x4d\x35\x3e\x2d'
        )

        # dbMask = MGF(seed, length(DB))
        db_mask = pkcs1_v2.mgf1(seed, length=len(db))
        expected_db_mask = (
            b'\x06\xe1\xde\xb2\x36\x9a\xa5\xa5\xc7\x07\xd8\x2c\x8e\x4e\x93\x24'
            b'\x8a\xc7\x83\xde\xe0\xb2\xc0\x46\x26\xf5\xaf\xf9\x3e\xdc\xfb\x25'
            b'\xc9\xc2\xb3\xff\x8a\xe1\x0e\x83\x9a\x2d\xdb\x4c\xdc\xfe\x4f\xf4'
            b'\x77\x28\xb4\xa1\xb7\xc1\x36\x2b\xaa\xd2\x9a\xb4\x8d\x28\x69\xd5'
            b'\x02\x41\x21\x43\x58\x11\x59\x1b\xe3\x92\xf9\x82\xfb\x3e\x87\xd0'
            b'\x95\xae\xb4\x04\x48\xdb\x97\x2f\x3a\xc1\x4e\xaf\xf4\x9c\x8c\x3b'
            b'\x7c\xfc\x95\x1a\x51\xec\xd1\xdd\xe6\x12\x64'
        )

        self.assertEqual(db_mask, expected_db_mask)

        # seedMask = MGF(maskedDB, length(seed))
        seed_mask = pkcs1_v2.mgf1(masked_db, length=len(seed))
        expected_seed_mask = (
            b'\x41\x87\x0b\x5a\xb0\x29\xe6\x57\xd9\x57\x50\xb5\x4c\x28\x3c\x08'
            b'\x72\x5d\xbe\xa9'
        )

        self.assertEqual(seed_mask, expected_seed_mask)

    def test_invalid_hasher(self):
        """Tests an invalid hasher generates an exception"""
        with self.assertRaises(ValueError):
            pkcs1_v2.mgf1(b'\x06\xe1\xde\xb2', length=8, hasher='SHA2')

    def test_invalid_length(self):
        with self.assertRaises(OverflowError):
            pkcs1_v2.mgf1(b'\x06\xe1\xde\xb2', length=2**50)
