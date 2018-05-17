from __future__ import division, absolute_import, print_function

import os
import sys
from tempfile import mkdtemp, mkstemp, NamedTemporaryFile
from shutil import rmtree

from numpy.compat import asbytes
from numpy.testing import (
    run_module_suite, TestCase, assert_, SkipTest
    )
import numpy.lib._datasource as datasource

if sys.version_info[0] >= 3:
    import urllib.request as urllib_request
    from urllib.parse import urlparse
    from urllib.error import URLError
else:
    import urllib2 as urllib_request
    from urlparse import urlparse
    from urllib2 import URLError


def urlopen_stub(url, data=None):
    '''Stub to replace urlopen for testing.'''
    if url == valid_httpurl():
        tmpfile = NamedTemporaryFile(prefix='urltmp_')
        return tmpfile
    else:
        raise URLError('Name or service not known')

# setup and teardown
old_urlopen = None


def setup():
    global old_urlopen

    old_urlopen = urllib_request.urlopen
    urllib_request.urlopen = urlopen_stub


def teardown():
    urllib_request.urlopen = old_urlopen

# A valid website for more robust testing
http_path = 'http://www.google.com/'
http_file = 'index.html'

http_fakepath = 'http://fake.abc.web/site/'
http_fakefile = 'fake.txt'

malicious_files = ['/etc/shadow', '../../shadow',
                   '..\\system.dat', 'c:\\windows\\system.dat']

magic_line = asbytes('three is the magic number')


# Utility functions used by many TestCases
def valid_textfile(filedir):
    # Generate and return a valid temporary file.
    fd, path = mkstemp(suffix='.txt', prefix='dstmp_', dir=filedir, text=True)
    os.close(fd)
    return path


def invalid_textfile(filedir):
    # Generate and return an invalid filename.
    fd, path = mkstemp(suffix='.txt', prefix='dstmp_', dir=filedir)
    os.close(fd)
    os.remove(path)
    return path


def valid_httpurl():
    return http_path+http_file


def invalid_httpurl():
    return http_fakepath+http_fakefile


def valid_baseurl():
    return http_path


def invalid_baseurl():
    return http_fakepath


def valid_httpfile():
    return http_file


def invalid_httpfile():
    return http_fakefile


class TestDataSourceOpen(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()
        self.ds = datasource.DataSource(self.tmpdir)

    def tearDown(self):
        rmtree(self.tmpdir)
        del self.ds

    def test_ValidHTTP(self):
        fh = self.ds.open(valid_httpurl())
        assert_(fh)
        fh.close()

    def test_InvalidHTTP(self):
        url = invalid_httpurl()
        self.assertRaises(IOError, self.ds.open, url)
        try:
            self.ds.open(url)
        except IOError as e:
            # Regression test for bug fixed in r4342.
            assert_(e.errno is None)

    def test_InvalidHTTPCacheURLError(self):
        self.assertRaises(URLError, self.ds._cache, invalid_httpurl())

    def test_ValidFile(self):
        local_file = valid_textfile(self.tmpdir)
        fh = self.ds.open(local_file)
        assert_(fh)
        fh.close()

    def test_InvalidFile(self):
        invalid_file = invalid_textfile(self.tmpdir)
        self.assertRaises(IOError, self.ds.open, invalid_file)

    def test_ValidGzipFile(self):
        try:
            import gzip
        except ImportError:
            # We don't have the gzip capabilities to test.
            raise SkipTest
        # Test datasource's internal file_opener for Gzip files.
        filepath = os.path.join(self.tmpdir, 'foobar.txt.gz')
        fp = gzip.open(filepath, 'w')
        fp.write(magic_line)
        fp.close()
        fp = self.ds.open(filepath)
        result = fp.readline()
        fp.close()
        self.assertEqual(magic_line, result)

    def test_ValidBz2File(self):
        try:
            import bz2
        except ImportError:
            # We don't have the bz2 capabilities to test.
            raise SkipTest
        # Test datasource's internal file_opener for BZip2 files.
        filepath = os.path.join(self.tmpdir, 'foobar.txt.bz2')
        fp = bz2.BZ2File(filepath, 'w')
        fp.write(magic_line)
        fp.close()
        fp = self.ds.open(filepath)
        result = fp.readline()
        fp.close()
        self.assertEqual(magic_line, result)


class TestDataSourceExists(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()
        self.ds = datasource.DataSource(self.tmpdir)

    def tearDown(self):
        rmtree(self.tmpdir)
        del self.ds

    def test_ValidHTTP(self):
        assert_(self.ds.exists(valid_httpurl()))

    def test_InvalidHTTP(self):
        self.assertEqual(self.ds.exists(invalid_httpurl()), False)

    def test_ValidFile(self):
        # Test valid file in destpath
        tmpfile = valid_textfile(self.tmpdir)
        assert_(self.ds.exists(tmpfile))
        # Test valid local file not in destpath
        localdir = mkdtemp()
        tmpfile = valid_textfile(localdir)
        assert_(self.ds.exists(tmpfile))
        rmtree(localdir)

    def test_InvalidFile(self):
        tmpfile = invalid_textfile(self.tmpdir)
        self.assertEqual(self.ds.exists(tmpfile), False)


class TestDataSourceAbspath(TestCase):
    def setUp(self):
        self.tmpdir = os.path.abspath(mkdtemp())
        self.ds = datasource.DataSource(self.tmpdir)

    def tearDown(self):
        rmtree(self.tmpdir)
        del self.ds

    def test_ValidHTTP(self):
        scheme, netloc, upath, pms, qry, frg = urlparse(valid_httpurl())
        local_path = os.path.join(self.tmpdir, netloc,
                                  upath.strip(os.sep).strip('/'))
        self.assertEqual(local_path, self.ds.abspath(valid_httpurl()))

    def test_ValidFile(self):
        tmpfile = valid_textfile(self.tmpdir)
        tmpfilename = os.path.split(tmpfile)[-1]
        # Test with filename only
        self.assertEqual(tmpfile, self.ds.abspath(tmpfilename))
        # Test filename with complete path
        self.assertEqual(tmpfile, self.ds.abspath(tmpfile))

    def test_InvalidHTTP(self):
        scheme, netloc, upath, pms, qry, frg = urlparse(invalid_httpurl())
        invalidhttp = os.path.join(self.tmpdir, netloc,
                                   upath.strip(os.sep).strip('/'))
        self.assertNotEqual(invalidhttp, self.ds.abspath(valid_httpurl()))

    def test_InvalidFile(self):
        invalidfile = valid_textfile(self.tmpdir)
        tmpfile = valid_textfile(self.tmpdir)
        tmpfilename = os.path.split(tmpfile)[-1]
        # Test with filename only
        self.assertNotEqual(invalidfile, self.ds.abspath(tmpfilename))
        # Test filename with complete path
        self.assertNotEqual(invalidfile, self.ds.abspath(tmpfile))

    def test_sandboxing(self):
        tmpfile = valid_textfile(self.tmpdir)
        tmpfilename = os.path.split(tmpfile)[-1]

        tmp_path = lambda x: os.path.abspath(self.ds.abspath(x))

        assert_(tmp_path(valid_httpurl()).startswith(self.tmpdir))
        assert_(tmp_path(invalid_httpurl()).startswith(self.tmpdir))
        assert_(tmp_path(tmpfile).startswith(self.tmpdir))
        assert_(tmp_path(tmpfilename).startswith(self.tmpdir))
        for fn in malicious_files:
            assert_(tmp_path(http_path+fn).startswith(self.tmpdir))
            assert_(tmp_path(fn).startswith(self.tmpdir))

    def test_windows_os_sep(self):
        orig_os_sep = os.sep
        try:
            os.sep = '\\'
            self.test_ValidHTTP()
            self.test_ValidFile()
            self.test_InvalidHTTP()
            self.test_InvalidFile()
            self.test_sandboxing()
        finally:
            os.sep = orig_os_sep


class TestRepositoryAbspath(TestCase):
    def setUp(self):
        self.tmpdir = os.path.abspath(mkdtemp())
        self.repos = datasource.Repository(valid_baseurl(), self.tmpdir)

    def tearDown(self):
        rmtree(self.tmpdir)
        del self.repos

    def test_ValidHTTP(self):
        scheme, netloc, upath, pms, qry, frg = urlparse(valid_httpurl())
        local_path = os.path.join(self.repos._destpath, netloc,
                                  upath.strip(os.sep).strip('/'))
        filepath = self.repos.abspath(valid_httpfile())
        self.assertEqual(local_path, filepath)

    def test_sandboxing(self):
        tmp_path = lambda x: os.path.abspath(self.repos.abspath(x))
        assert_(tmp_path(valid_httpfile()).startswith(self.tmpdir))
        for fn in malicious_files:
            assert_(tmp_path(http_path+fn).startswith(self.tmpdir))
            assert_(tmp_path(fn).startswith(self.tmpdir))

    def test_windows_os_sep(self):
        orig_os_sep = os.sep
        try:
            os.sep = '\\'
            self.test_ValidHTTP()
            self.test_sandboxing()
        finally:
            os.sep = orig_os_sep


class TestRepositoryExists(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()
        self.repos = datasource.Repository(valid_baseurl(), self.tmpdir)

    def tearDown(self):
        rmtree(self.tmpdir)
        del self.repos

    def test_ValidFile(self):
        # Create local temp file
        tmpfile = valid_textfile(self.tmpdir)
        assert_(self.repos.exists(tmpfile))

    def test_InvalidFile(self):
        tmpfile = invalid_textfile(self.tmpdir)
        self.assertEqual(self.repos.exists(tmpfile), False)

    def test_RemoveHTTPFile(self):
        assert_(self.repos.exists(valid_httpurl()))

    def test_CachedHTTPFile(self):
        localfile = valid_httpurl()
        # Create a locally cached temp file with an URL based
        # directory structure.  This is similar to what Repository.open
        # would do.
        scheme, netloc, upath, pms, qry, frg = urlparse(localfile)
        local_path = os.path.join(self.repos._destpath, netloc)
        os.mkdir(local_path, 0o0700)
        tmpfile = valid_textfile(local_path)
        assert_(self.repos.exists(tmpfile))


class TestOpenFunc(TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()

    def tearDown(self):
        rmtree(self.tmpdir)

    def test_DataSourceOpen(self):
        local_file = valid_textfile(self.tmpdir)
        # Test case where destpath is passed in
        fp = datasource.open(local_file, destpath=self.tmpdir)
        assert_(fp)
        fp.close()
        # Test case where default destpath is used
        fp = datasource.open(local_file)
        assert_(fp)
        fp.close()


if __name__ == "__main__":
    run_module_suite()
