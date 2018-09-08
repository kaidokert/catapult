# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


import setuptools
import sys


package_data = {
  '': ['devil_dependencies.json']
}

if sys.platform == 'linux2':
  package_data[''].append('bin/deps/linux2/x86_64/bin/*')


setuptools.setup(
    name='devil',

    version='0.1.0',

    description='A device interaction library',

    url='https://github.com/catapult-project/catapult/tree/master/devil',

    author='The Chromium Authors',
    author_email='chromium-dev@chromium.org',

    license='Custom',

    classifiers=[
        'Development Status :: 4 - Beta',
        # See the LICENSE file.
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 2.7',
    ],

    packages=setuptools.find_packages(),

    package_data=package_data,
)
