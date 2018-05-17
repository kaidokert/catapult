from __future__ import division, absolute_import, print_function

import pickle
import warnings

import numpy
import numpy as np
import datetime
from numpy.compat import asbytes
from numpy.testing import (
    TestCase, run_module_suite, assert_, assert_equal, assert_raises,
    assert_warns, dec
)

# Use pytz to test out various time zones if available
try:
    from pytz import timezone as tz
    _has_pytz = True
except ImportError:
    _has_pytz = False


class TestDateTime(TestCase):
    def test_datetime_dtype_creation(self):
        for unit in ['Y', 'M', 'W', 'D',
                     'h', 'm', 's', 'ms', 'us',
                     'ns', 'ps', 'fs', 'as']:
            dt1 = np.dtype('M8[750%s]' % unit)
            assert_(dt1 == np.dtype('datetime64[750%s]' % unit))
            dt2 = np.dtype('m8[%s]' % unit)
            assert_(dt2 == np.dtype('timedelta64[%s]' % unit))

        # Generic units shouldn't add [] to the end
        assert_equal(str(np.dtype("M8")), "datetime64")

        # Should be possible to specify the endianness
        assert_equal(np.dtype("=M8"), np.dtype("M8"))
        assert_equal(np.dtype("=M8[s]"), np.dtype("M8[s]"))
        assert_(np.dtype(">M8") == np.dtype("M8") or
                np.dtype("<M8") == np.dtype("M8"))
        assert_(np.dtype(">M8[D]") == np.dtype("M8[D]") or
                np.dtype("<M8[D]") == np.dtype("M8[D]"))
        assert_(np.dtype(">M8") != np.dtype("<M8"))

        assert_equal(np.dtype("=m8"), np.dtype("m8"))
        assert_equal(np.dtype("=m8[s]"), np.dtype("m8[s]"))
        assert_(np.dtype(">m8") == np.dtype("m8") or
                np.dtype("<m8") == np.dtype("m8"))
        assert_(np.dtype(">m8[D]") == np.dtype("m8[D]") or
                np.dtype("<m8[D]") == np.dtype("m8[D]"))
        assert_(np.dtype(">m8") != np.dtype("<m8"))

        # Check that the parser rejects bad datetime types
        assert_raises(TypeError, np.dtype, 'M8[badunit]')
        assert_raises(TypeError, np.dtype, 'm8[badunit]')
        assert_raises(TypeError, np.dtype, 'M8[YY]')
        assert_raises(TypeError, np.dtype, 'm8[YY]')
        assert_raises(TypeError, np.dtype, 'm4')
        assert_raises(TypeError, np.dtype, 'M7')
        assert_raises(TypeError, np.dtype, 'm7')
        assert_raises(TypeError, np.dtype, 'M16')
        assert_raises(TypeError, np.dtype, 'm16')

    def test_datetime_casting_rules(self):
        # Cannot cast safely/same_kind between timedelta and datetime
        assert_(not np.can_cast('m8', 'M8', casting='same_kind'))
        assert_(not np.can_cast('M8', 'm8', casting='same_kind'))
        assert_(not np.can_cast('m8', 'M8', casting='safe'))
        assert_(not np.can_cast('M8', 'm8', casting='safe'))

        # Can cast safely/same_kind from integer to timedelta
        assert_(np.can_cast('i8', 'm8', casting='same_kind'))
        assert_(np.can_cast('i8', 'm8', casting='safe'))

        # Cannot cast safely/same_kind from float to timedelta
        assert_(not np.can_cast('f4', 'm8', casting='same_kind'))
        assert_(not np.can_cast('f4', 'm8', casting='safe'))

        # Cannot cast safely/same_kind from integer to datetime
        assert_(not np.can_cast('i8', 'M8', casting='same_kind'))
        assert_(not np.can_cast('i8', 'M8', casting='safe'))

        # Cannot cast safely/same_kind from bool to datetime
        assert_(not np.can_cast('b1', 'M8', casting='same_kind'))
        assert_(not np.can_cast('b1', 'M8', casting='safe'))
        # Can cast safely/same_kind from bool to timedelta
        assert_(np.can_cast('b1', 'm8', casting='same_kind'))
        assert_(np.can_cast('b1', 'm8', casting='safe'))

        # Can cast datetime safely from months/years to days
        assert_(np.can_cast('M8[M]', 'M8[D]', casting='safe'))
        assert_(np.can_cast('M8[Y]', 'M8[D]', casting='safe'))
        # Cannot cast timedelta safely from months/years to days
        assert_(not np.can_cast('m8[M]', 'm8[D]', casting='safe'))
        assert_(not np.can_cast('m8[Y]', 'm8[D]', casting='safe'))
        # Can cast datetime same_kind from months/years to days
        assert_(np.can_cast('M8[M]', 'M8[D]', casting='same_kind'))
        assert_(np.can_cast('M8[Y]', 'M8[D]', casting='same_kind'))
        # Can't cast timedelta same_kind from months/years to days
        assert_(not np.can_cast('m8[M]', 'm8[D]', casting='same_kind'))
        assert_(not np.can_cast('m8[Y]', 'm8[D]', casting='same_kind'))
        # Can cast datetime same_kind across the date/time boundary
        assert_(np.can_cast('M8[D]', 'M8[h]', casting='same_kind'))
        # Can cast timedelta same_kind across the date/time boundary
        assert_(np.can_cast('m8[D]', 'm8[h]', casting='same_kind'))
        assert_(np.can_cast('m8[h]', 'm8[D]', casting='same_kind'))

        # Cannot cast safely if the integer multiplier doesn't divide
        assert_(not np.can_cast('M8[7h]', 'M8[3h]', casting='safe'))
        assert_(not np.can_cast('M8[3h]', 'M8[6h]', casting='safe'))
        # But can cast same_kind
        assert_(np.can_cast('M8[7h]', 'M8[3h]', casting='same_kind'))
        # Can cast safely if the integer multiplier does divide
        assert_(np.can_cast('M8[6h]', 'M8[3h]', casting='safe'))

        # We can always cast types with generic units (corresponding to NaT) to
        # more specific types
        assert_(np.can_cast('m8', 'm8[h]', casting='same_kind'))
        assert_(np.can_cast('m8', 'm8[h]', casting='safe'))
        assert_(np.can_cast('M8', 'M8[h]', casting='same_kind'))
        assert_(np.can_cast('M8', 'M8[h]', casting='safe'))
        # but not the other way around
        assert_(not np.can_cast('m8[h]', 'm8', casting='same_kind'))
        assert_(not np.can_cast('m8[h]', 'm8', casting='safe'))
        assert_(not np.can_cast('M8[h]', 'M8', casting='same_kind'))
        assert_(not np.can_cast('M8[h]', 'M8', casting='safe'))

    def test_compare_generic_nat(self):
        # regression tests for GH6452
        assert_equal(np.datetime64('NaT'),
                     np.datetime64('2000') + np.timedelta64('NaT'))
        # nb. we may want to make NaT != NaT true in the future; this test
        # verifies the existing behavior (and that it should not warn)
        assert_(np.datetime64('NaT') == np.datetime64('NaT', 'us'))
        assert_(np.datetime64('NaT', 'us') == np.datetime64('NaT'))

    def test_datetime_scalar_construction(self):
        # Construct with different units
        assert_equal(np.datetime64('1950-03-12', 'D'),
                     np.datetime64('1950-03-12'))
        assert_equal(np.datetime64('1950-03-12T13', 's'),
                     np.datetime64('1950-03-12T13', 'm'))

        # Default construction means NaT
        assert_equal(np.datetime64(), np.datetime64('NaT'))

        # Some basic strings and repr
        assert_equal(str(np.datetime64('NaT')), 'NaT')
        assert_equal(repr(np.datetime64('NaT')),
                     "numpy.datetime64('NaT')")
        assert_equal(str(np.datetime64('2011-02')), '2011-02')
        assert_equal(repr(np.datetime64('2011-02')),
                     "numpy.datetime64('2011-02')")

        # None gets constructed as NaT
        assert_equal(np.datetime64(None), np.datetime64('NaT'))

        # Default construction of NaT is in generic units
        assert_equal(np.datetime64().dtype, np.dtype('M8'))
        assert_equal(np.datetime64('NaT').dtype, np.dtype('M8'))

        # Construction from integers requires a specified unit
        assert_raises(ValueError, np.datetime64, 17)

        # When constructing from a scalar or zero-dimensional array,
        # it either keeps the units or you can override them.
        a = np.datetime64('2000-03-18T16', 'h')
        b = np.array('2000-03-18T16', dtype='M8[h]')

        assert_equal(a.dtype, np.dtype('M8[h]'))
        assert_equal(b.dtype, np.dtype('M8[h]'))

        assert_equal(np.datetime64(a), a)
        assert_equal(np.datetime64(a).dtype, np.dtype('M8[h]'))

        assert_equal(np.datetime64(b), a)
        assert_equal(np.datetime64(b).dtype, np.dtype('M8[h]'))

        assert_equal(np.datetime64(a, 's'), a)
        assert_equal(np.datetime64(a, 's').dtype, np.dtype('M8[s]'))

        assert_equal(np.datetime64(b, 's'), a)
        assert_equal(np.datetime64(b, 's').dtype, np.dtype('M8[s]'))

        # Construction from datetime.date
        assert_equal(np.datetime64('1945-03-25'),
                     np.datetime64(datetime.date(1945, 3, 25)))
        assert_equal(np.datetime64('2045-03-25', 'D'),
                     np.datetime64(datetime.date(2045, 3, 25), 'D'))
        # Construction from datetime.datetime
        assert_equal(np.datetime64('1980-01-25T14:36:22.5'),
                     np.datetime64(datetime.datetime(1980, 1, 25,
                                                14, 36, 22, 500000)))

        # Construction with time units from a date is okay
        assert_equal(np.datetime64('1920-03-13', 'h'),
                     np.datetime64('1920-03-13T00'))
        assert_equal(np.datetime64('1920-03', 'm'),
                     np.datetime64('1920-03-01T00:00'))
        assert_equal(np.datetime64('1920', 's'),
                     np.datetime64('1920-01-01T00:00:00'))
        assert_equal(np.datetime64(datetime.date(2045, 3, 25), 'ms'),
                     np.datetime64('2045-03-25T00:00:00.000'))

        # Construction with date units from a datetime is also okay
        assert_equal(np.datetime64('1920-03-13T18', 'D'),
                     np.datetime64('1920-03-13'))
        assert_equal(np.datetime64('1920-03-13T18:33:12', 'M'),
                     np.datetime64('1920-03'))
        assert_equal(np.datetime64('1920-03-13T18:33:12.5', 'Y'),
                     np.datetime64('1920'))

    def test_datetime_scalar_construction_timezone(self):
        # verify that supplying an explicit timezone works, but is deprecated
        with assert_warns(DeprecationWarning):
            assert_equal(np.datetime64('2000-01-01T00Z'),
                         np.datetime64('2000-01-01T00'))
        with assert_warns(DeprecationWarning):
            assert_equal(np.datetime64('2000-01-01T00-08'),
                         np.datetime64('2000-01-01T08'))

    def test_datetime_array_find_type(self):
        dt = np.datetime64('1970-01-01', 'M')
        arr = np.array([dt])
        assert_equal(arr.dtype, np.dtype('M8[M]'))

        # at the moment, we don't automatically convert these to datetime64

        dt = datetime.date(1970, 1, 1)
        arr = np.array([dt])
        assert_equal(arr.dtype, np.dtype('O'))

        dt = datetime.datetime(1970, 1, 1, 12, 30, 40)
        arr = np.array([dt])
        assert_equal(arr.dtype, np.dtype('O'))

        # find "supertype" for non-dates and dates

        b = np.bool_(True)
        dt = np.datetime64('1970-01-01', 'M')
        arr = np.array([b, dt])
        assert_equal(arr.dtype, np.dtype('O'))

        dt = datetime.date(1970, 1, 1)
        arr = np.array([b, dt])
        assert_equal(arr.dtype, np.dtype('O'))

        dt = datetime.datetime(1970, 1, 1, 12, 30, 40)
        arr = np.array([b, dt])
        assert_equal(arr.dtype, np.dtype('O'))

    def test_timedelta_scalar_construction(self):
        # Construct with different units
        assert_equal(np.timedelta64(7, 'D'),
                     np.timedelta64(1, 'W'))
        assert_equal(np.timedelta64(120, 's'),
                     np.timedelta64(2, 'm'))

        # Default construction means 0
        assert_equal(np.timedelta64(), np.timedelta64(0))

        # None gets constructed as NaT
        assert_equal(np.timedelta64(None), np.timedelta64('NaT'))

        # Some basic strings and repr
        assert_equal(str(np.timedelta64('NaT')), 'NaT')
        assert_equal(repr(np.timedelta64('NaT')),
                     "numpy.timedelta64('NaT')")
        assert_equal(str(np.timedelta64(3, 's')), '3 seconds')
        assert_equal(repr(np.timedelta64(-3, 's')),
                     "numpy.timedelta64(-3,'s')")
        assert_equal(repr(np.timedelta64(12)),
                     "numpy.timedelta64(12)")

        # Construction from an integer produces generic units
        assert_equal(np.timedelta64(12).dtype, np.dtype('m8'))

        # When constructing from a scalar or zero-dimensional array,
        # it either keeps the units or you can override them.
        a = np.timedelta64(2, 'h')
        b = np.array(2, dtype='m8[h]')

        assert_equal(a.dtype, np.dtype('m8[h]'))
        assert_equal(b.dtype, np.dtype('m8[h]'))

        assert_equal(np.timedelta64(a), a)
        assert_equal(np.timedelta64(a).dtype, np.dtype('m8[h]'))

        assert_equal(np.timedelta64(b), a)
        assert_equal(np.timedelta64(b).dtype, np.dtype('m8[h]'))

        assert_equal(np.timedelta64(a, 's'), a)
        assert_equal(np.timedelta64(a, 's').dtype, np.dtype('m8[s]'))

        assert_equal(np.timedelta64(b, 's'), a)
        assert_equal(np.timedelta64(b, 's').dtype, np.dtype('m8[s]'))

        # Construction from datetime.timedelta
        assert_equal(np.timedelta64(5, 'D'),
                     np.timedelta64(datetime.timedelta(days=5)))
        assert_equal(np.timedelta64(102347621, 's'),
                     np.timedelta64(datetime.timedelta(seconds=102347621)))
        assert_equal(np.timedelta64(-10234760000, 'us'),
                     np.timedelta64(datetime.timedelta(
                                            microseconds=-10234760000)))
        assert_equal(np.timedelta64(10234760000, 'us'),
                     np.timedelta64(datetime.timedelta(
                                            microseconds=10234760000)))
        assert_equal(np.timedelta64(1023476, 'ms'),
                     np.timedelta64(datetime.timedelta(milliseconds=1023476)))
        assert_equal(np.timedelta64(10, 'm'),
                     np.timedelta64(datetime.timedelta(minutes=10)))
        assert_equal(np.timedelta64(281, 'h'),
                     np.timedelta64(datetime.timedelta(hours=281)))
        assert_equal(np.timedelta64(28, 'W'),
                     np.timedelta64(datetime.timedelta(weeks=28)))

        # Cannot construct across nonlinear time unit boundaries
        a = np.timedelta64(3, 's')
        assert_raises(TypeError, np.timedelta64, a, 'M')
        assert_raises(TypeError, np.timedelta64, a, 'Y')
        a = np.timedelta64(6, 'M')
        assert_raises(TypeError, np.timedelta64, a, 'D')
        assert_raises(TypeError, np.timedelta64, a, 'h')
        a = np.timedelta64(1, 'Y')
        assert_raises(TypeError, np.timedelta64, a, 'D')
        assert_raises(TypeError, np.timedelta64, a, 'm')

    def test_timedelta_scalar_construction_units(self):
        # String construction detecting units
        assert_equal(np.datetime64('2010').dtype,
                     np.dtype('M8[Y]'))
        assert_equal(np.datetime64('2010-03').dtype,
                     np.dtype('M8[M]'))
        assert_equal(np.datetime64('2010-03-12').dtype,
                     np.dtype('M8[D]'))
        assert_equal(np.datetime64('2010-03-12T17').dtype,
                     np.dtype('M8[h]'))
        assert_equal(np.datetime64('2010-03-12T17:15').dtype,
                     np.dtype('M8[m]'))
        assert_equal(np.datetime64('2010-03-12T17:15:08').dtype,
                     np.dtype('M8[s]'))

        assert_equal(np.datetime64('2010-03-12T17:15:08.1').dtype,
                     np.dtype('M8[ms]'))
        assert_equal(np.datetime64('2010-03-12T17:15:08.12').dtype,
                     np.dtype('M8[ms]'))
        assert_equal(np.datetime64('2010-03-12T17:15:08.123').dtype,
                     np.dtype('M8[ms]'))

        assert_equal(np.datetime64('2010-03-12T17:15:08.1234').dtype,
                     np.dtype('M8[us]'))
        assert_equal(np.datetime64('2010-03-12T17:15:08.12345').dtype,
                     np.dtype('M8[us]'))
        assert_equal(np.datetime64('2010-03-12T17:15:08.123456').dtype,
                     np.dtype('M8[us]'))

        assert_equal(np.datetime64('1970-01-01T00:00:02.1234567').dtype,
                     np.dtype('M8[ns]'))
        assert_equal(np.datetime64('1970-01-01T00:00:02.12345678').dtype,
                     np.dtype('M8[ns]'))
        assert_equal(np.datetime64('1970-01-01T00:00:02.123456789').dtype,
                     np.dtype('M8[ns]'))

        assert_equal(np.datetime64('1970-01-01T00:00:02.1234567890').dtype,
                     np.dtype('M8[ps]'))
        assert_equal(np.datetime64('1970-01-01T00:00:02.12345678901').dtype,
                     np.dtype('M8[ps]'))
        assert_equal(np.datetime64('1970-01-01T00:00:02.123456789012').dtype,
                     np.dtype('M8[ps]'))

        assert_equal(np.datetime64(
                     '1970-01-01T00:00:02.1234567890123').dtype,
                     np.dtype('M8[fs]'))
        assert_equal(np.datetime64(
                     '1970-01-01T00:00:02.12345678901234').dtype,
                     np.dtype('M8[fs]'))
        assert_equal(np.datetime64(
                     '1970-01-01T00:00:02.123456789012345').dtype,
                     np.dtype('M8[fs]'))

        assert_equal(np.datetime64(
                    '1970-01-01T00:00:02.1234567890123456').dtype,
                     np.dtype('M8[as]'))
        assert_equal(np.datetime64(
                    '1970-01-01T00:00:02.12345678901234567').dtype,
                     np.dtype('M8[as]'))
        assert_equal(np.datetime64(
                    '1970-01-01T00:00:02.123456789012345678').dtype,
                     np.dtype('M8[as]'))

        # Python date object
        assert_equal(np.datetime64(datetime.date(2010, 4, 16)).dtype,
                     np.dtype('M8[D]'))

        # Python datetime object
        assert_equal(np.datetime64(
                        datetime.datetime(2010, 4, 16, 13, 45, 18)).dtype,
                     np.dtype('M8[us]'))

        # 'today' special value
        assert_equal(np.datetime64('today').dtype,
                     np.dtype('M8[D]'))

        # 'now' special value
        assert_equal(np.datetime64('now').dtype,
                     np.dtype('M8[s]'))

    def test_datetime_nat_casting(self):
        a = np.array('NaT', dtype='M8[D]')
        b = np.datetime64('NaT', '[D]')

        # Arrays
        assert_equal(a.astype('M8[s]'), np.array('NaT', dtype='M8[s]'))
        assert_equal(a.astype('M8[ms]'), np.array('NaT', dtype='M8[ms]'))
        assert_equal(a.astype('M8[M]'), np.array('NaT', dtype='M8[M]'))
        assert_equal(a.astype('M8[Y]'), np.array('NaT', dtype='M8[Y]'))
        assert_equal(a.astype('M8[W]'), np.array('NaT', dtype='M8[W]'))

        # Scalars -> Scalars
        assert_equal(np.datetime64(b, '[s]'), np.datetime64('NaT', '[s]'))
        assert_equal(np.datetime64(b, '[ms]'), np.datetime64('NaT', '[ms]'))
        assert_equal(np.datetime64(b, '[M]'), np.datetime64('NaT', '[M]'))
        assert_equal(np.datetime64(b, '[Y]'), np.datetime64('NaT', '[Y]'))
        assert_equal(np.datetime64(b, '[W]'), np.datetime64('NaT', '[W]'))

        # Arrays -> Scalars
        assert_equal(np.datetime64(a, '[s]'), np.datetime64('NaT', '[s]'))
        assert_equal(np.datetime64(a, '[ms]'), np.datetime64('NaT', '[ms]'))
        assert_equal(np.datetime64(a, '[M]'), np.datetime64('NaT', '[M]'))
        assert_equal(np.datetime64(a, '[Y]'), np.datetime64('NaT', '[Y]'))
        assert_equal(np.datetime64(a, '[W]'), np.datetime64('NaT', '[W]'))

    def test_days_creation(self):
        assert_equal(np.array('1599', dtype='M8[D]').astype('i8'),
                (1600-1970)*365 - (1972-1600)/4 + 3 - 365)
        assert_equal(np.array('1600', dtype='M8[D]').astype('i8'),
                (1600-1970)*365 - (1972-1600)/4 + 3)
        assert_equal(np.array('1601', dtype='M8[D]').astype('i8'),
                (1600-1970)*365 - (1972-1600)/4 + 3 + 366)
        assert_equal(np.array('1900', dtype='M8[D]').astype('i8'),
                (1900-1970)*365 - (1970-1900)//4)
        assert_equal(np.array('1901', dtype='M8[D]').astype('i8'),
                (1900-1970)*365 - (1970-1900)//4 + 365)
        assert_equal(np.array('1967', dtype='M8[D]').astype('i8'), -3*365 - 1)
        assert_equal(np.array('1968', dtype='M8[D]').astype('i8'), -2*365 - 1)
        assert_equal(np.array('1969', dtype='M8[D]').astype('i8'), -1*365)
        assert_equal(np.array('1970', dtype='M8[D]').astype('i8'), 0*365)
        assert_equal(np.array('1971', dtype='M8[D]').astype('i8'), 1*365)
        assert_equal(np.array('1972', dtype='M8[D]').astype('i8'), 2*365)
        assert_equal(np.array('1973', dtype='M8[D]').astype('i8'), 3*365 + 1)
        assert_equal(np.array('1974', dtype='M8[D]').astype('i8'), 4*365 + 1)
        assert_equal(np.array('2000', dtype='M8[D]').astype('i8'),
                 (2000 - 1970)*365 + (2000 - 1972)//4)
        assert_equal(np.array('2001', dtype='M8[D]').astype('i8'),
                 (2000 - 1970)*365 + (2000 - 1972)//4 + 366)
        assert_equal(np.array('2400', dtype='M8[D]').astype('i8'),
                 (2400 - 1970)*365 + (2400 - 1972)//4 - 3)
        assert_equal(np.array('2401', dtype='M8[D]').astype('i8'),
                 (2400 - 1970)*365 + (2400 - 1972)//4 - 3 + 366)

        assert_equal(np.array('1600-02-29', dtype='M8[D]').astype('i8'),
                (1600-1970)*365 - (1972-1600)//4 + 3 + 31 + 28)
        assert_equal(np.array('1600-03-01', dtype='M8[D]').astype('i8'),
                (1600-1970)*365 - (1972-1600)//4 + 3 + 31 + 29)
        assert_equal(np.array('2000-02-29', dtype='M8[D]').astype('i8'),
                 (2000 - 1970)*365 + (2000 - 1972)//4 + 31 + 28)
        assert_equal(np.array('2000-03-01', dtype='M8[D]').astype('i8'),
                 (2000 - 1970)*365 + (2000 - 1972)//4 + 31 + 29)
        assert_equal(np.array('2001-03-22', dtype='M8[D]').astype('i8'),
                 (2000 - 1970)*365 + (2000 - 1972)//4 + 366 + 31 + 28 + 21)

    def test_days_to_pydate(self):
        assert_equal(np.array('1599', dtype='M8[D]').astype('O'),
                    datetime.date(1599, 1, 1))
        assert_equal(np.array('1600', dtype='M8[D]').astype('O'),
                    datetime.date(1600, 1, 1))
        assert_equal(np.array('1601', dtype='M8[D]').astype('O'),
                    datetime.date(1601, 1, 1))
        assert_equal(np.array('1900', dtype='M8[D]').astype('O'),
                    datetime.date(1900, 1, 1))
        assert_equal(np.array('1901', dtype='M8[D]').astype('O'),
                    datetime.date(1901, 1, 1))
        assert_equal(np.array('2000', dtype='M8[D]').astype('O'),
                    datetime.date(2000, 1, 1))
        assert_equal(np.array('2001', dtype='M8[D]').astype('O'),
                    datetime.date(2001, 1, 1))
        assert_equal(np.array('1600-02-29', dtype='M8[D]').astype('O'),
                    datetime.date(1600, 2, 29))
        assert_equal(np.array('1600-03-01', dtype='M8[D]').astype('O'),
                    datetime.date(1600, 3, 1))
        assert_equal(np.array('2001-03-22', dtype='M8[D]').astype('O'),
                    datetime.date(2001, 3, 22))

    def test_dtype_comparison(self):
        assert_(not (np.dtype('M8[us]') == np.dtype('M8[ms]')))
        assert_(np.dtype('M8[us]') != np.dtype('M8[ms]'))
        assert_(np.dtype('M8[2D]') != np.dtype('M8[D]'))
        assert_(np.dtype('M8[D]') != np.dtype('M8[2D]'))

    def test_pydatetime_creation(self):
        a = np.array(['1960-03-12', datetime.date(1960, 3, 12)], dtype='M8[D]')
        assert_equal(a[0], a[1])
        a = np.array(['1999-12-31', datetime.date(1999, 12, 31)], dtype='M8[D]')
        assert_equal(a[0], a[1])
        a = np.array(['2000-01-01', datetime.date(2000, 1, 1)], dtype='M8[D]')
        assert_equal(a[0], a[1])
        # Will fail if the date changes during the exact right moment
        a = np.array(['today', datetime.date.today()], dtype='M8[D]')
        assert_equal(a[0], a[1])
        # datetime.datetime.now() returns local time, not UTC
        #a = np.array(['now', datetime.datetime.now()], dtype='M8[s]')
        #assert_equal(a[0], a[1])

        # we can give a datetime.date time units
        assert_equal(np.array(datetime.date(1960, 3, 12), dtype='M8[s]'),
                     np.array(np.datetime64('1960-03-12T00:00:00')))

    def test_datetime_string_conversion(self):
        a = ['2011-03-16', '1920-01-01', '2013-05-19']
        str_a = np.array(a, dtype='S')
        dt_a = np.array(a, dtype='M')
        str_b = np.empty_like(str_a)
        dt_b = np.empty_like(dt_a)

        # String to datetime
        assert_equal(dt_a, str_a.astype('M'))
        assert_equal(dt_a.dtype, str_a.astype('M').dtype)
        dt_b[...] = str_a
        assert_equal(dt_a, dt_b)
        # Datetime to string
        assert_equal(str_a, dt_a.astype('S0'))
        str_b[...] = dt_a
        assert_equal(str_a, str_b)

        # Convert the 'S' to 'U'
        str_a = str_a.astype('U')
        str_b = str_b.astype('U')

        # Unicode to datetime
        assert_equal(dt_a, str_a.astype('M'))
        assert_equal(dt_a.dtype, str_a.astype('M').dtype)
        dt_b[...] = str_a
        assert_equal(dt_a, dt_b)
        # Datetime to unicode
        assert_equal(str_a, dt_a.astype('U'))
        str_b[...] = dt_a
        assert_equal(str_a, str_b)

    def test_datetime_array_str(self):
        a = np.array(['2011-03-16', '1920-01-01', '2013-05-19'], dtype='M')
        assert_equal(str(a), "['2011-03-16' '1920-01-01' '2013-05-19']")

        a = np.array(['2011-03-16T13:55', '1920-01-01T03:12'], dtype='M')
        assert_equal(np.array2string(a, separator=', ',
                    formatter={'datetime': lambda x:
                            "'%s'" % np.datetime_as_string(x, timezone='UTC')}),
                     "['2011-03-16T13:55Z', '1920-01-01T03:12Z']")

        # Check that one NaT doesn't corrupt subsequent entries
        a = np.array(['2010', 'NaT', '2030']).astype('M')
        assert_equal(str(a), "['2010' 'NaT' '2030']")

    def test_timedelta_array_str(self):
        a = np.array([-1, 0, 100], dtype='m')
        assert_equal(str(a), "[ -1   0 100]")
        a = np.array(['NaT', 'NaT'], dtype='m')
        assert_equal(str(a), "['NaT' 'NaT']")
        # Check right-alignment with NaTs
        a = np.array([-1, 'NaT', 0], dtype='m')
        assert_equal(str(a), "[   -1 'NaT'     0]")
        a = np.array([-1, 'NaT', 1234567], dtype='m')
        assert_equal(str(a), "[     -1   'NaT' 1234567]")

    def test_pickle(self):
        # Check that pickle roundtripping works
        dt = np.dtype('M8[7D]')
        assert_equal(pickle.loads(pickle.dumps(dt)), dt)
        dt = np.dtype('M8[W]')
        assert_equal(pickle.loads(pickle.dumps(dt)), dt)

        # Check that loading pickles from 1.6 works
        pkl = "cnumpy\ndtype\np0\n(S'M8'\np1\nI0\nI1\ntp2\nRp3\n" + \
              "(I4\nS'<'\np4\nNNNI-1\nI-1\nI0\n((dp5\n(S'D'\np6\n" + \
              "I7\nI1\nI1\ntp7\ntp8\ntp9\nb."
        assert_equal(pickle.loads(asbytes(pkl)), np.dtype('<M8[7D]'))
        pkl = "cnumpy\ndtype\np0\n(S'M8'\np1\nI0\nI1\ntp2\nRp3\n" + \
              "(I4\nS'<'\np4\nNNNI-1\nI-1\nI0\n((dp5\n(S'W'\np6\n" + \
              "I1\nI1\nI1\ntp7\ntp8\ntp9\nb."
        assert_equal(pickle.loads(asbytes(pkl)), np.dtype('<M8[W]'))
        pkl = "cnumpy\ndtype\np0\n(S'M8'\np1\nI0\nI1\ntp2\nRp3\n" + \
              "(I4\nS'>'\np4\nNNNI-1\nI-1\nI0\n((dp5\n(S'us'\np6\n" + \
              "I1\nI1\nI1\ntp7\ntp8\ntp9\nb."
        assert_equal(pickle.loads(asbytes(pkl)), np.dtype('>M8[us]'))

    def test_setstate(self):
        "Verify that datetime dtype __setstate__ can handle bad arguments"
        dt = np.dtype('>M8[us]')
        assert_raises(ValueError, dt.__setstate__, (4, '>', None, None, None, -1, -1, 0, 1))
        assert_(dt.__reduce__()[2] == np.dtype('>M8[us]').__reduce__()[2])
        assert_raises(TypeError, dt.__setstate__, (4, '>', None, None, None, -1, -1, 0, ({}, 'xxx')))
        assert_(dt.__reduce__()[2] == np.dtype('>M8[us]').__reduce__()[2])

    def test_dtype_promotion(self):
        # datetime <op> datetime computes the metadata gcd
        # timedelta <op> timedelta computes the metadata gcd
        for mM in ['m', 'M']:
            assert_equal(
                np.promote_types(np.dtype(mM+'8[2Y]'), np.dtype(mM+'8[2Y]')),
                np.dtype(mM+'8[2Y]'))
            assert_equal(
                np.promote_types(np.dtype(mM+'8[12Y]'), np.dtype(mM+'8[15Y]')),
                np.dtype(mM+'8[3Y]'))
            assert_equal(
                np.promote_types(np.dtype(mM+'8[62M]'), np.dtype(mM+'8[24M]')),
                np.dtype(mM+'8[2M]'))
            assert_equal(
                np.promote_types(np.dtype(mM+'8[1W]'), np.dtype(mM+'8[2D]')),
                np.dtype(mM+'8[1D]'))
            assert_equal(
                np.promote_types(np.dtype(mM+'8[W]'), np.dtype(mM+'8[13s]')),
                np.dtype(mM+'8[s]'))
            assert_equal(
                np.promote_types(np.dtype(mM+'8[13W]'), np.dtype(mM+'8[49s]')),
                np.dtype(mM+'8[7s]'))
        # timedelta <op> timedelta raises when there is no reasonable gcd
        assert_raises(TypeError, np.promote_types,
                            np.dtype('m8[Y]'), np.dtype('m8[D]'))
        assert_raises(TypeError, np.promote_types,
                            np.dtype('m8[M]'), np.dtype('m8[W]'))
        # timedelta <op> timedelta may overflow with big unit ranges
        assert_raises(OverflowError, np.promote_types,
                            np.dtype('m8[W]'), np.dtype('m8[fs]'))
        assert_raises(OverflowError, np.promote_types,
                            np.dtype('m8[s]'), np.dtype('m8[as]'))

    def test_cast_overflow(self):
        # gh-4486
        def cast():
            numpy.datetime64("1971-01-01 00:00:00.000000000000000").astype("<M8[D]")
        assert_raises(OverflowError, cast)

        def cast2():
            numpy.datetime64("2014").astype("<M8[fs]")
        assert_raises(OverflowError, cast2)

    def test_pyobject_roundtrip(self):
        # All datetime types should be able to roundtrip through object
        a = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0,
                      -1020040340, -2942398, -1, 0, 1, 234523453, 1199164176],
                                                        dtype=np.int64)
        # With date units
        for unit in ['M8[D]', 'M8[W]', 'M8[M]', 'M8[Y]']:
            b = a.copy().view(dtype=unit)
            b[0] = '-0001-01-01'
            b[1] = '-0001-12-31'
            b[2] = '0000-01-01'
            b[3] = '0001-01-01'
            b[4] = '1969-12-31'
            b[5] = '1970-01-01'
            b[6] = '9999-12-31'
            b[7] = '10000-01-01'
            b[8] = 'NaT'

            assert_equal(b.astype(object).astype(unit), b,
                            "Error roundtripping unit %s" % unit)
        # With time units
        for unit in ['M8[as]', 'M8[16fs]', 'M8[ps]', 'M8[us]',
                     'M8[300as]', 'M8[20us]']:
            b = a.copy().view(dtype=unit)
            b[0] = '-0001-01-01T00'
            b[1] = '-0001-12-31T00'
            b[2] = '0000-01-01T00'
            b[3] = '0001-01-01T00'
            b[4] = '1969-12-31T23:59:59.999999'
            b[5] = '1970-01-01T00'
            b[6] = '9999-12-31T23:59:59.999999'
            b[7] = '10000-01-01T00'
            b[8] = 'NaT'

            assert_equal(b.astype(object).astype(unit), b,
                            "Error roundtripping unit %s" % unit)

    def test_month_truncation(self):
        # Make sure that months are truncating correctly
        assert_equal(np.array('1945-03-01', dtype='M8[M]'),
                     np.array('1945-03-31', dtype='M8[M]'))
        assert_equal(np.array('1969-11-01', dtype='M8[M]'),
             np.array('1969-11-30T23:59:59.99999', dtype='M').astype('M8[M]'))
        assert_equal(np.array('1969-12-01', dtype='M8[M]'),
             np.array('1969-12-31T23:59:59.99999', dtype='M').astype('M8[M]'))
        assert_equal(np.array('1970-01-01', dtype='M8[M]'),
             np.array('1970-01-31T23:59:59.99999', dtype='M').astype('M8[M]'))
        assert_equal(np.array('1980-02-01', dtype='M8[M]'),
             np.array('1980-02-29T23:59:59.99999', dtype='M').astype('M8[M]'))

    def test_different_unit_comparison(self):
        # Check some years with date units
        for unit1 in ['Y', 'M', 'D']:
            dt1 = np.dtype('M8[%s]' % unit1)
            for unit2 in ['Y', 'M', 'D']:
                dt2 = np.dtype('M8[%s]' % unit2)
                assert_equal(np.array('1945', dtype=dt1),
                             np.array('1945', dtype=dt2))
                assert_equal(np.array('1970', dtype=dt1),
                             np.array('1970', dtype=dt2))
                assert_equal(np.array('9999', dtype=dt1),
                             np.array('9999', dtype=dt2))
                assert_equal(np.array('10000', dtype=dt1),
                             np.array('10000-01-01', dtype=dt2))
                assert_equal(np.datetime64('1945', unit1),
                             np.datetime64('1945', unit2))
                assert_equal(np.datetime64('1970', unit1),
                             np.datetime64('1970', unit2))
                assert_equal(np.datetime64('9999', unit1),
                             np.datetime64('9999', unit2))
                assert_equal(np.datetime64('10000', unit1),
                             np.datetime64('10000-01-01', unit2))
        # Check some datetimes with time units
        for unit1 in ['6h', 'h', 'm', 's', '10ms', 'ms', 'us']:
            dt1 = np.dtype('M8[%s]' % unit1)
            for unit2 in ['h', 'm', 's', 'ms', 'us']:
                dt2 = np.dtype('M8[%s]' % unit2)
                assert_equal(np.array('1945-03-12T18', dtype=dt1),
                             np.array('1945-03-12T18', dtype=dt2))
                assert_equal(np.array('1970-03-12T18', dtype=dt1),
                             np.array('1970-03-12T18', dtype=dt2))
                assert_equal(np.array('9999-03-12T18', dtype=dt1),
                             np.array('9999-03-12T18', dtype=dt2))
                assert_equal(np.array('10000-01-01T00', dtype=dt1),
                             np.array('10000-01-01T00', dtype=dt2))
                assert_equal(np.datetime64('1945-03-12T18', unit1),
                             np.datetime64('1945-03-12T18', unit2))
                assert_equal(np.datetime64('1970-03-12T18', unit1),
                             np.datetime64('1970-03-12T18', unit2))
                assert_equal(np.datetime64('9999-03-12T18', unit1),
                             np.datetime64('9999-03-12T18', unit2))
                assert_equal(np.datetime64('10000-01-01T00', unit1),
                             np.datetime64('10000-01-01T00', unit2))
        # Check some days with units that won't overflow
        for unit1 in ['D', '12h', 'h', 'm', 's', '4s', 'ms', 'us']:
            dt1 = np.dtype('M8[%s]' % unit1)
            for unit2 in ['D', 'h', 'm', 's', 'ms', 'us']:
                dt2 = np.dtype('M8[%s]' % unit2)
                assert_(np.equal(np.array('1932-02-17', dtype='M').astype(dt1),
                     np.array('1932-02-17T00:00:00', dtype='M').astype(dt2),
                     casting='unsafe'))
                assert_(np.equal(np.array('10000-04-27', dtype='M').astype(dt1),
                     np.array('10000-04-27T00:00:00', dtype='M').astype(dt2),
                     casting='unsafe'))

        # Shouldn't be able to compare datetime and timedelta
        # TODO: Changing to 'same_kind' or 'safe' casting in the ufuncs by
        #       default is needed to properly catch this kind of thing...
        a = np.array('2012-12-21', dtype='M8[D]')
        b = np.array(3, dtype='m8[D]')
        #assert_raises(TypeError, np.less, a, b)
        assert_raises(TypeError, np.less, a, b, casting='same_kind')

    def test_datetime_like(self):
        a = np.array([3], dtype='m8[4D]')
        b = np.array(['2012-12-21'], dtype='M8[D]')

        assert_equal(np.ones_like(a).dtype, a.dtype)
        assert_equal(np.zeros_like(a).dtype, a.dtype)
        assert_equal(np.empty_like(a).dtype, a.dtype)
        assert_equal(np.ones_like(b).dtype, b.dtype)
        assert_equal(np.zeros_like(b).dtype, b.dtype)
        assert_equal(np.empty_like(b).dtype, b.dtype)

    def test_datetime_unary(self):
        for tda, tdb, tdzero, tdone, tdmone in \
                [
                 # One-dimensional arrays
                 (np.array([3], dtype='m8[D]'),
                  np.array([-3], dtype='m8[D]'),
                  np.array([0], dtype='m8[D]'),
                  np.array([1], dtype='m8[D]'),
                  np.array([-1], dtype='m8[D]')),
                 # NumPy scalars
                 (np.timedelta64(3, '[D]'),
                  np.timedelta64(-3, '[D]'),
                  np.timedelta64(0, '[D]'),
                  np.timedelta64(1, '[D]'),
                  np.timedelta64(-1, '[D]'))]:
            # negative ufunc
            assert_equal(-tdb, tda)
            assert_equal((-tdb).dtype, tda.dtype)
            assert_equal(np.negative(tdb), tda)
            assert_equal(np.negative(tdb).dtype, tda.dtype)

            # absolute ufunc
            assert_equal(np.absolute(tdb), tda)
            assert_equal(np.absolute(tdb).dtype, tda.dtype)

            # sign ufunc
            assert_equal(np.sign(tda), tdone)
            assert_equal(np.sign(tdb), tdmone)
            assert_equal(np.sign(tdzero), tdzero)
            assert_equal(np.sign(tda).dtype, tda.dtype)

            # The ufuncs always produce native-endian results
            assert_

    def test_datetime_add(self):
        for dta, dtb, dtc, dtnat, tda, tdb, tdc in \
                    [
                     # One-dimensional arrays
                     (np.array(['2012-12-21'], dtype='M8[D]'),
                      np.array(['2012-12-24'], dtype='M8[D]'),
                      np.array(['2012-12-21T11'], dtype='M8[h]'),
                      np.array(['NaT'], dtype='M8[D]'),
                      np.array([3], dtype='m8[D]'),
                      np.array([11], dtype='m8[h]'),
                      np.array([3*24 + 11], dtype='m8[h]')),
                     # NumPy scalars
                     (np.datetime64('2012-12-21', '[D]'),
                      np.datetime64('2012-12-24', '[D]'),
                      np.datetime64('2012-12-21T11', '[h]'),
                      np.datetime64('NaT', '[D]'),
                      np.timedelta64(3, '[D]'),
                      np.timedelta64(11, '[h]'),
                      np.timedelta64(3*24 + 11, '[h]'))]:
            # m8 + m8
            assert_equal(tda + tdb, tdc)
            assert_equal((tda + tdb).dtype, np.dtype('m8[h]'))
            # m8 + bool
            assert_equal(tdb + True, tdb + 1)
            assert_equal((tdb + True).dtype, np.dtype('m8[h]'))
            # m8 + int
            assert_equal(tdb + 3*24, tdc)
            assert_equal((tdb + 3*24).dtype, np.dtype('m8[h]'))
            # bool + m8
            assert_equal(False + tdb, tdb)
            assert_equal((False + tdb).dtype, np.dtype('m8[h]'))
            # int + m8
            assert_equal(3*24 + tdb, tdc)
            assert_equal((3*24 + tdb).dtype, np.dtype('m8[h]'))
            # M8 + bool
            assert_equal(dta + True, dta + 1)
            assert_equal(dtnat + True, dtnat)
            assert_equal((dta + True).dtype, np.dtype('M8[D]'))
            # M8 + int
            assert_equal(dta + 3, dtb)
            assert_equal(dtnat + 3, dtnat)
            assert_equal((dta + 3).dtype, np.dtype('M8[D]'))
            # bool + M8
            assert_equal(False + dta, dta)
            assert_equal(False + dtnat, dtnat)
            assert_equal((False + dta).dtype, np.dtype('M8[D]'))
            # int + M8
            assert_equal(3 + dta, dtb)
            assert_equal(3 + dtnat, dtnat)
            assert_equal((3 + dta).dtype, np.dtype('M8[D]'))
            # M8 + m8
            assert_equal(dta + tda, dtb)
            assert_equal(dtnat + tda, dtnat)
            assert_equal((dta + tda).dtype, np.dtype('M8[D]'))
            # m8 + M8
            assert_equal(tda + dta, dtb)
            assert_equal(tda + dtnat, dtnat)
            assert_equal((tda + dta).dtype, np.dtype('M8[D]'))

            # In M8 + m8, the result goes to higher precision
            assert_equal(np.add(dta, tdb, casting='unsafe'), dtc)
            assert_equal(np.add(dta, tdb, casting='unsafe').dtype,
                         np.dtype('M8[h]'))
            assert_equal(np.add(tdb, dta, casting='unsafe'), dtc)
            assert_equal(np.add(tdb, dta, casting='unsafe').dtype,
                         np.dtype('M8[h]'))

            # M8 + M8
            assert_raises(TypeError, np.add, dta, dtb)

    def test_datetime_subtract(self):
        for dta, dtb, dtc, dtd, dte, dtnat, tda, tdb, tdc in \
                    [
                     # One-dimensional arrays
                     (np.array(['2012-12-21'], dtype='M8[D]'),
                      np.array(['2012-12-24'], dtype='M8[D]'),
                      np.array(['1940-12-24'], dtype='M8[D]'),
                      np.array(['1940-12-24T00'], dtype='M8[h]'),
                      np.array(['1940-12-23T13'], dtype='M8[h]'),
                      np.array(['NaT'], dtype='M8[D]'),
                      np.array([3], dtype='m8[D]'),
                      np.array([11], dtype='m8[h]'),
                      np.array([3*24 - 11], dtype='m8[h]')),
                     # NumPy scalars
                     (np.datetime64('2012-12-21', '[D]'),
                      np.datetime64('2012-12-24', '[D]'),
                      np.datetime64('1940-12-24', '[D]'),
                      np.datetime64('1940-12-24T00', '[h]'),
                      np.datetime64('1940-12-23T13', '[h]'),
                      np.datetime64('NaT', '[D]'),
                      np.timedelta64(3, '[D]'),
                      np.timedelta64(11, '[h]'),
                      np.timedelta64(3*24 - 11, '[h]'))]:
            # m8 - m8
            assert_equal(tda - tdb, tdc)
            assert_equal((tda - tdb).dtype, np.dtype('m8[h]'))
            assert_equal(tdb - tda, -tdc)
            assert_equal((tdb - tda).dtype, np.dtype('m8[h]'))
            # m8 - bool
            assert_equal(tdc - True, tdc - 1)
            assert_equal((tdc - True).dtype, np.dtype('m8[h]'))
            # m8 - int
            assert_equal(tdc - 3*24, -tdb)
            assert_equal((tdc - 3*24).dtype, np.dtype('m8[h]'))
            # int - m8
            assert_equal(False - tdb, -tdb)
            assert_equal((False - tdb).dtype, np.dtype('m8[h]'))
            # int - m8
            assert_equal(3*24 - tdb, tdc)
            assert_equal((3*24 - tdb).dtype, np.dtype('m8[h]'))
            # M8 - bool
            assert_equal(dtb - True, dtb - 1)
            assert_equal(dtnat - True, dtnat)
            assert_equal((dtb - True).dtype, np.dtype('M8[D]'))
            # M8 - int
            assert_equal(dtb - 3, dta)
            assert_equal(dtnat - 3, dtnat)
            assert_equal((dtb - 3).dtype, np.dtype('M8[D]'))
            # M8 - m8
            assert_equal(dtb - tda, dta)
            assert_equal(dtnat - tda, dtnat)
            assert_equal((dtb - tda).dtype, np.dtype('M8[D]'))

            # In M8 - m8, the result goes to higher precision
            assert_equal(np.subtract(dtc, tdb, casting='unsafe'), dte)
            assert_equal(np.subtract(dtc, tdb, casting='unsafe').dtype,
                         np.dtype('M8[h]'))

            # M8 - M8 with different goes to higher precision
            assert_equal(np.subtract(dtc, dtd, casting='unsafe'),
                         np.timedelta64(0, 'h'))
            assert_equal(np.subtract(dtc, dtd, casting='unsafe').dtype,
                         np.dtype('m8[h]'))
            assert_equal(np.subtract(dtd, dtc, casting='unsafe'),
                         np.timedelta64(0, 'h'))
            assert_equal(np.subtract(dtd, dtc, casting='unsafe').dtype,
                         np.dtype('m8[h]'))

            # m8 - M8
            assert_raises(TypeError, np.subtract, tda, dta)
            # bool - M8
            assert_raises(TypeError, np.subtract, False, dta)
            # int - M8
            assert_raises(TypeError, np.subtract, 3, dta)

    def test_datetime_multiply(self):
        for dta, tda, tdb, tdc in \
                    [
                     # One-dimensional arrays
                     (np.array(['2012-12-21'], dtype='M8[D]'),
                      np.array([6], dtype='m8[h]'),
                      np.array([9], dtype='m8[h]'),
                      np.array([12], dtype='m8[h]')),
                     # NumPy scalars
                     (np.datetime64('2012-12-21', '[D]'),
                      np.timedelta64(6, '[h]'),
                      np.timedelta64(9, '[h]'),
                      np.timedelta64(12, '[h]'))]:
            # m8 * int
            assert_equal(tda * 2, tdc)
            assert_equal((tda * 2).dtype, np.dtype('m8[h]'))
            # int * m8
            assert_equal(2 * tda, tdc)
            assert_equal((2 * tda).dtype, np.dtype('m8[h]'))
            # m8 * float
            assert_equal(tda * 1.5, tdb)
            assert_equal((tda * 1.5).dtype, np.dtype('m8[h]'))
            # float * m8
            assert_equal(1.5 * tda, tdb)
            assert_equal((1.5 * tda).dtype, np.dtype('m8[h]'))

            # m8 * m8
            assert_raises(TypeError, np.multiply, tda, tdb)
            # m8 * M8
            assert_raises(TypeError, np.multiply, dta, tda)
            # M8 * m8
            assert_raises(TypeError, np.multiply, tda, dta)
            # M8 * int
            assert_raises(TypeError, np.multiply, dta, 2)
            # int * M8
            assert_raises(TypeError, np.multiply, 2, dta)
            # M8 * float
            assert_raises(TypeError, np.multiply, dta, 1.5)
            # float * M8
            assert_raises(TypeError, np.multiply, 1.5, dta)

        # NaTs
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            nat = np.timedelta64('NaT')
            def check(a, b, res):
                assert_equal(a * b, res)
                assert_equal(b * a, res)
            for tp in (int, float):
                check(nat, tp(2), nat)
                check(nat, tp(0), nat)
            for f in (float('inf'), float('nan')):
                check(np.timedelta64(1), f, nat)
                check(np.timedelta64(0), f, nat)
                check(nat, f, nat)

    def test_datetime_divide(self):
        for dta, tda, tdb, tdc, tdd in \
                    [
                     # One-dimensional arrays
                     (np.array(['2012-12-21'], dtype='M8[D]'),
                      np.array([6], dtype='m8[h]'),
                      np.array([9], dtype='m8[h]'),
                      np.array([12], dtype='m8[h]'),
                      np.array([6], dtype='m8[m]')),
                     # NumPy scalars
                     (np.datetime64('2012-12-21', '[D]'),
                      np.timedelta64(6, '[h]'),
                      np.timedelta64(9, '[h]'),
                      np.timedelta64(12, '[h]'),
                      np.timedelta64(6, '[m]'))]:
            # m8 / int
            assert_equal(tdc / 2, tda)
            assert_equal((tdc / 2).dtype, np.dtype('m8[h]'))
            # m8 / float
            assert_equal(tda / 0.5, tdc)
            assert_equal((tda / 0.5).dtype, np.dtype('m8[h]'))
            # m8 / m8
            assert_equal(tda / tdb, 6.0 / 9.0)
            assert_equal(np.divide(tda, tdb), 6.0 / 9.0)
            assert_equal(np.true_divide(tda, tdb), 6.0 / 9.0)
            assert_equal(tdb / tda, 9.0 / 6.0)
            assert_equal((tda / tdb).dtype, np.dtype('f8'))
            assert_equal(tda / tdd, 60.0)
            assert_equal(tdd / tda, 1.0 / 60.0)

            # m8 // m8
            assert_raises(TypeError, np.floor_divide, tda, tdb)
            # int / m8
            assert_raises(TypeError, np.divide, 2, tdb)
            # float / m8
            assert_raises(TypeError, np.divide, 0.5, tdb)
            # m8 / M8
            assert_raises(TypeError, np.divide, dta, tda)
            # M8 / m8
            assert_raises(TypeError, np.divide, tda, dta)
            # M8 / int
            assert_raises(TypeError, np.divide, dta, 2)
            # int / M8
            assert_raises(TypeError, np.divide, 2, dta)
            # M8 / float
            assert_raises(TypeError, np.divide, dta, 1.5)
            # float / M8
            assert_raises(TypeError, np.divide, 1.5, dta)

        # NaTs
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            nat = np.timedelta64('NaT')
            for tp in (int, float):
                assert_equal(np.timedelta64(1) / tp(0), nat)
                assert_equal(np.timedelta64(0) / tp(0), nat)
                assert_equal(nat / tp(0), nat)
                assert_equal(nat / tp(2), nat)
            # Division by inf
            assert_equal(np.timedelta64(1) / float('inf'), np.timedelta64(0))
            assert_equal(np.timedelta64(0) / float('inf'), np.timedelta64(0))
            assert_equal(nat / float('inf'), nat)
            # Division by nan
            assert_equal(np.timedelta64(1) / float('nan'), nat)
            assert_equal(np.timedelta64(0) / float('nan'), nat)
            assert_equal(nat / float('nan'), nat)

    def test_datetime_compare(self):
        # Test all the comparison operators
        a = np.datetime64('2000-03-12T18:00:00.000000')
        b = np.array(['2000-03-12T18:00:00.000000',
                      '2000-03-12T17:59:59.999999',
                      '2000-03-12T18:00:00.000001',
                      '1970-01-11T12:00:00.909090',
                      '2016-01-11T12:00:00.909090'],
                      dtype='datetime64[us]')
        assert_equal(np.equal(a, b), [1, 0, 0, 0, 0])
        assert_equal(np.not_equal(a, b), [0, 1, 1, 1, 1])
        assert_equal(np.less(a, b), [0, 0, 1, 0, 1])
        assert_equal(np.less_equal(a, b), [1, 0, 1, 0, 1])
        assert_equal(np.greater(a, b), [0, 1, 0, 1, 0])
        assert_equal(np.greater_equal(a, b), [1, 1, 0, 1, 0])

    def test_datetime_compare_nat(self):
        dt_nat = np.datetime64('NaT', 'D')
        dt_other = np.datetime64('2000-01-01')
        td_nat = np.timedelta64('NaT', 'h')
        td_other = np.timedelta64(1, 'h')

        for op in [np.equal, np.less, np.less_equal,
                   np.greater, np.greater_equal]:
            if op(dt_nat, dt_nat):
                assert_warns(FutureWarning, op, dt_nat, dt_nat)
            if op(dt_nat, dt_other):
                assert_warns(FutureWarning, op, dt_nat, dt_other)
            if op(dt_other, dt_nat):
                assert_warns(FutureWarning, op, dt_other, dt_nat)
            if op(td_nat, td_nat):
                assert_warns(FutureWarning, op, td_nat, td_nat)
            if op(td_nat, td_other):
                assert_warns(FutureWarning, op, td_nat, td_other)
            if op(td_other, td_nat):
                assert_warns(FutureWarning, op, td_other, td_nat)

        assert_warns(FutureWarning, np.not_equal, dt_nat, dt_nat)
        assert_(np.not_equal(dt_nat, dt_other))
        assert_(np.not_equal(dt_other, dt_nat))
        assert_warns(FutureWarning, np.not_equal, td_nat, td_nat)
        assert_(np.not_equal(td_nat, td_other))
        assert_(np.not_equal(td_other, td_nat))

    def test_datetime_minmax(self):
        # The metadata of the result should become the GCD
        # of the operand metadata
        a = np.array('1999-03-12T13', dtype='M8[2m]')
        b = np.array('1999-03-12T12', dtype='M8[s]')
        assert_equal(np.minimum(a, b), b)
        assert_equal(np.minimum(a, b).dtype, np.dtype('M8[s]'))
        assert_equal(np.fmin(a, b), b)
        assert_equal(np.fmin(a, b).dtype, np.dtype('M8[s]'))
        assert_equal(np.maximum(a, b), a)
        assert_equal(np.maximum(a, b).dtype, np.dtype('M8[s]'))
        assert_equal(np.fmax(a, b), a)
        assert_equal(np.fmax(a, b).dtype, np.dtype('M8[s]'))
        # Viewed as integers, the comparison is opposite because
        # of the units chosen
        assert_equal(np.minimum(a.view('i8'), b.view('i8')), a.view('i8'))

        # Interaction with NaT
        a = np.array('1999-03-12T13', dtype='M8[2m]')
        dtnat = np.array('NaT', dtype='M8[h]')
        assert_equal(np.minimum(a, dtnat), a)
        assert_equal(np.minimum(dtnat, a), a)
        assert_equal(np.maximum(a, dtnat), a)
        assert_equal(np.maximum(dtnat, a), a)

        # Also do timedelta
        a = np.array(3, dtype='m8[h]')
        b = np.array(3*3600 - 3, dtype='m8[s]')
        assert_equal(np.minimum(a, b), b)
        assert_equal(np.minimum(a, b).dtype, np.dtype('m8[s]'))
        assert_equal(np.fmin(a, b), b)
        assert_equal(np.fmin(a, b).dtype, np.dtype('m8[s]'))
        assert_equal(np.maximum(a, b), a)
        assert_equal(np.maximum(a, b).dtype, np.dtype('m8[s]'))
        assert_equal(np.fmax(a, b), a)
        assert_equal(np.fmax(a, b).dtype, np.dtype('m8[s]'))
        # Viewed as integers, the comparison is opposite because
        # of the units chosen
        assert_equal(np.minimum(a.view('i8'), b.view('i8')), a.view('i8'))

        # should raise between datetime and timedelta
        #
        # TODO: Allowing unsafe casting by
        #       default in ufuncs strikes again... :(
        a = np.array(3, dtype='m8[h]')
        b = np.array('1999-03-12T12', dtype='M8[s]')
        #assert_raises(TypeError, np.minimum, a, b)
        #assert_raises(TypeError, np.maximum, a, b)
        #assert_raises(TypeError, np.fmin, a, b)
        #assert_raises(TypeError, np.fmax, a, b)
        assert_raises(TypeError, np.minimum, a, b, casting='same_kind')
        assert_raises(TypeError, np.maximum, a, b, casting='same_kind')
        assert_raises(TypeError, np.fmin, a, b, casting='same_kind')
        assert_raises(TypeError, np.fmax, a, b, casting='same_kind')

    def test_hours(self):
        t = np.ones(3, dtype='M8[s]')
        t[0] = 60*60*24 + 60*60*10
        assert_(t[0].item().hour == 10)

    def test_divisor_conversion_year(self):
        assert_(np.dtype('M8[Y/4]') == np.dtype('M8[3M]'))
        assert_(np.dtype('M8[Y/13]') == np.dtype('M8[4W]'))
        assert_(np.dtype('M8[3Y/73]') == np.dtype('M8[15D]'))

    def test_divisor_conversion_month(self):
        assert_(np.dtype('M8[M/2]') == np.dtype('M8[2W]'))
        assert_(np.dtype('M8[M/15]') == np.dtype('M8[2D]'))
        assert_(np.dtype('M8[3M/40]') == np.dtype('M8[54h]'))

    def test_divisor_conversion_week(self):
        assert_(np.dtype('m8[W/7]') == np.dtype('m8[D]'))
        assert_(np.dtype('m8[3W/14]') == np.dtype('m8[36h]'))
        assert_(np.dtype('m8[5W/140]') == np.dtype('m8[360m]'))

    def test_divisor_conversion_day(self):
        assert_(np.dtype('M8[D/12]') == np.dtype('M8[2h]'))
        assert_(np.dtype('M8[D/120]') == np.dtype('M8[12m]'))
        assert_(np.dtype('M8[3D/960]') == np.dtype('M8[270s]'))

    def test_divisor_conversion_hour(self):
        assert_(np.dtype('m8[h/30]') == np.dtype('m8[2m]'))
        assert_(np.dtype('m8[3h/300]') == np.dtype('m8[36s]'))

    def test_divisor_conversion_minute(self):
        assert_(np.dtype('m8[m/30]') == np.dtype('m8[2s]'))
        assert_(np.dtype('m8[3m/300]') == np.dtype('m8[600ms]'))

    def test_divisor_conversion_second(self):
        assert_(np.dtype('m8[s/100]') == np.dtype('m8[10ms]'))
        assert_(np.dtype('m8[3s/10000]') == np.dtype('m8[300us]'))

    def test_divisor_conversion_fs(self):
        assert_(np.dtype('M8[fs/100]') == np.dtype('M8[10as]'))
        self.assertRaises(ValueError, lambda: np.dtype('M8[3fs/10000]'))

    def test_divisor_conversion_as(self):
        self.assertRaises(ValueError, lambda: np.dtype('M8[as/10]'))

    def test_string_parser_variants(self):
        # Allow space instead of 'T' between date and time
        assert_equal(np.array(['1980-02-29T01:02:03'], np.dtype('M8[s]')),
                     np.array(['1980-02-29 01:02:03'], np.dtype('M8[s]')))
        # Allow negative years
        assert_equal(np.array(['-1980-02-29T01:02:03'], np.dtype('M8[s]')),
                     np.array(['-1980-02-29 01:02:03'], np.dtype('M8[s]')))
        # UTC specifier
        with assert_warns(DeprecationWarning):
            assert_equal(
                np.array(['-1980-02-29T01:02:03'], np.dtype('M8[s]')),
                np.array(['-1980-02-29 01:02:03Z'], np.dtype('M8[s]')))
        # Time zone offset
        with assert_warns(DeprecationWarning):
            assert_equal(
                np.array(['1980-02-29T02:02:03'], np.dtype('M8[s]')),
                np.array(['1980-02-29 00:32:03-0130'], np.dtype('M8[s]')))
        with assert_warns(DeprecationWarning):
            assert_equal(
                np.array(['1980-02-28T22:32:03'], np.dtype('M8[s]')),
                np.array(['1980-02-29 00:02:03+01:30'], np.dtype('M8[s]')))
        with assert_warns(DeprecationWarning):
            assert_equal(
                np.array(['1980-02-29T02:32:03.506'], np.dtype('M8[s]')),
                np.array(['1980-02-29 00:32:03.506-02'], np.dtype('M8[s]')))
        with assert_warns(DeprecationWarning):
            assert_equal(np.datetime64('1977-03-02T12:30-0230'),
                         np.datetime64('1977-03-02T15:00'))

    def test_string_parser_error_check(self):
        # Arbitrary bad string
        assert_raises(ValueError, np.array, ['badvalue'], np.dtype('M8[us]'))
        # Character after year must be '-'
        assert_raises(ValueError, np.array, ['1980X'], np.dtype('M8[us]'))
        # Cannot have trailing '-'
        assert_raises(ValueError, np.array, ['1980-'], np.dtype('M8[us]'))
        # Month must be in range [1,12]
        assert_raises(ValueError, np.array, ['1980-00'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-13'], np.dtype('M8[us]'))
        # Month must have two digits
        assert_raises(ValueError, np.array, ['1980-1'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-1-02'], np.dtype('M8[us]'))
        # 'Mor' is not a valid month
        assert_raises(ValueError, np.array, ['1980-Mor'], np.dtype('M8[us]'))
        # Cannot have trailing '-'
        assert_raises(ValueError, np.array, ['1980-01-'], np.dtype('M8[us]'))
        # Day must be in range [1,len(month)]
        assert_raises(ValueError, np.array, ['1980-01-0'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-01-00'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-01-32'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1979-02-29'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-30'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-03-32'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-04-31'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-05-32'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-06-31'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-07-32'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-08-32'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-09-31'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-10-32'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-11-31'], np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-12-32'], np.dtype('M8[us]'))
        # Cannot have trailing characters
        assert_raises(ValueError, np.array, ['1980-02-03%'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03 q'],
                                                        np.dtype('M8[us]'))

        # Hours must be in range [0, 23]
        assert_raises(ValueError, np.array, ['1980-02-03 25'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03T25'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03 24:01'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03T24:01'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03 -1'],
                                                        np.dtype('M8[us]'))
        # No trailing ':'
        assert_raises(ValueError, np.array, ['1980-02-03 01:'],
                                                        np.dtype('M8[us]'))
        # Minutes must be in range [0, 59]
        assert_raises(ValueError, np.array, ['1980-02-03 01:-1'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03 01:60'],
                                                        np.dtype('M8[us]'))
        # No trailing ':'
        assert_raises(ValueError, np.array, ['1980-02-03 01:60:'],
                                                        np.dtype('M8[us]'))
        # Seconds must be in range [0, 59]
        assert_raises(ValueError, np.array, ['1980-02-03 01:10:-1'],
                                                        np.dtype('M8[us]'))
        assert_raises(ValueError, np.array, ['1980-02-03 01:01:60'],
                                                        np.dtype('M8[us]'))
        # Timezone offset must within a reasonable range
        with assert_warns(DeprecationWarning):
            assert_raises(ValueError, np.array, ['1980-02-03 01:01:00+0661'],
                                                            np.dtype('M8[us]'))
        with assert_warns(DeprecationWarning):
            assert_raises(ValueError, np.array, ['1980-02-03 01:01:00+2500'],
                                                            np.dtype('M8[us]'))
        with assert_warns(DeprecationWarning):
            assert_raises(ValueError, np.array, ['1980-02-03 01:01:00-0070'],
                                                            np.dtype('M8[us]'))
        with assert_warns(DeprecationWarning):
            assert_raises(ValueError, np.array, ['1980-02-03 01:01:00-3000'],
                                                            np.dtype('M8[us]'))
        with assert_warns(DeprecationWarning):
            assert_raises(ValueError, np.array, ['1980-02-03 01:01:00-25:00'],
                                                            np.dtype('M8[us]'))

    def test_creation_overflow(self):
        date = '1980-03-23 20:00:00'
        timesteps = np.array([date], dtype='datetime64[s]')[0].astype(np.int64)
        for unit in ['ms', 'us', 'ns']:
            timesteps *= 1000
            x = np.array([date], dtype='datetime64[%s]' % unit)

            assert_equal(timesteps, x[0].astype(np.int64),
                         err_msg='Datetime conversion error for unit %s' % unit)

        assert_equal(x[0].astype(np.int64), 322689600000000000)

    def test_datetime_as_string(self):
        # Check all the units with default string conversion
        date = '1959-10-13'
        datetime = '1959-10-13T12:34:56.789012345678901234'

        assert_equal(np.datetime_as_string(np.datetime64(date, 'Y')),
                     '1959')
        assert_equal(np.datetime_as_string(np.datetime64(date, 'M')),
                     '1959-10')
        assert_equal(np.datetime_as_string(np.datetime64(date, 'D')),
                     '1959-10-13')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'h')),
                     '1959-10-13T12')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'm')),
                     '1959-10-13T12:34')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 's')),
                     '1959-10-13T12:34:56')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'ms')),
                     '1959-10-13T12:34:56.789')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'us')),
                     '1959-10-13T12:34:56.789012')

        datetime = '1969-12-31T23:34:56.789012345678901234'

        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'ns')),
                     '1969-12-31T23:34:56.789012345')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'ps')),
                     '1969-12-31T23:34:56.789012345678')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'fs')),
                     '1969-12-31T23:34:56.789012345678901')

        datetime = '1969-12-31T23:59:57.789012345678901234'

        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'as')),
                     datetime)
        datetime = '1970-01-01T00:34:56.789012345678901234'

        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'ns')),
                     '1970-01-01T00:34:56.789012345')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'ps')),
                     '1970-01-01T00:34:56.789012345678')
        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'fs')),
                     '1970-01-01T00:34:56.789012345678901')

        datetime = '1970-01-01T00:00:05.789012345678901234'

        assert_equal(np.datetime_as_string(np.datetime64(datetime, 'as')),
                     datetime)

        # String conversion with the unit= parameter
        a = np.datetime64('2032-07-18T12:23:34.123456', 'us')
        assert_equal(np.datetime_as_string(a, unit='Y', casting='unsafe'),
                            '2032')
        assert_equal(np.datetime_as_string(a, unit='M', casting='unsafe'),
                            '2032-07')
        assert_equal(np.datetime_as_string(a, unit='W', casting='unsafe'),
                            '2032-07-18')
        assert_equal(np.datetime_as_string(a, unit='D', casting='unsafe'),
                            '2032-07-18')
        assert_equal(np.datetime_as_string(a, unit='h'), '2032-07-18T12')
        assert_equal(np.datetime_as_string(a, unit='m'),
                            '2032-07-18T12:23')
        assert_equal(np.datetime_as_string(a, unit='s'),
                            '2032-07-18T12:23:34')
        assert_equal(np.datetime_as_string(a, unit='ms'),
                            '2032-07-18T12:23:34.123')
        assert_equal(np.datetime_as_string(a, unit='us'),
                            '2032-07-18T12:23:34.123456')
        assert_equal(np.datetime_as_string(a, unit='ns'),
                            '2032-07-18T12:23:34.123456000')
        assert_equal(np.datetime_as_string(a, unit='ps'),
                            '2032-07-18T12:23:34.123456000000')
        assert_equal(np.datetime_as_string(a, unit='fs'),
                            '2032-07-18T12:23:34.123456000000000')
        assert_equal(np.datetime_as_string(a, unit='as'),
                            '2032-07-18T12:23:34.123456000000000000')

        # unit='auto' parameter
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-18T12:23:34.123456', 'us'), unit='auto'),
                '2032-07-18T12:23:34.123456')
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-18T12:23:34.12', 'us'), unit='auto'),
                '2032-07-18T12:23:34.120')
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-18T12:23:34', 'us'), unit='auto'),
                '2032-07-18T12:23:34')
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-18T12:23:00', 'us'), unit='auto'),
                '2032-07-18T12:23')
        # 'auto' doesn't split up hour and minute
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-18T12:00:00', 'us'), unit='auto'),
                '2032-07-18T12:00')
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-18T00:00:00', 'us'), unit='auto'),
                '2032-07-18')
        # 'auto' doesn't split up the date
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-07-01T00:00:00', 'us'), unit='auto'),
                '2032-07-01')
        assert_equal(np.datetime_as_string(
                np.datetime64('2032-01-01T00:00:00', 'us'), unit='auto'),
                '2032-01-01')

    @dec.skipif(not _has_pytz, "The pytz module is not available.")
    def test_datetime_as_string_timezone(self):
        # timezone='local' vs 'UTC'
        a = np.datetime64('2010-03-15T06:30', 'm')
        assert_equal(np.datetime_as_string(a),
                '2010-03-15T06:30')
        assert_equal(np.datetime_as_string(a, timezone='naive'),
                '2010-03-15T06:30')
        assert_equal(np.datetime_as_string(a, timezone='UTC'),
                '2010-03-15T06:30Z')
        assert_(np.datetime_as_string(a, timezone='local') !=
                '2010-03-15T06:30')

        b = np.datetime64('2010-02-15T06:30', 'm')

        assert_equal(np.datetime_as_string(a, timezone=tz('US/Central')),
                     '2010-03-15T01:30-0500')
        assert_equal(np.datetime_as_string(a, timezone=tz('US/Eastern')),
                     '2010-03-15T02:30-0400')
        assert_equal(np.datetime_as_string(a, timezone=tz('US/Pacific')),
                     '2010-03-14T23:30-0700')

        assert_equal(np.datetime_as_string(b, timezone=tz('US/Central')),
                     '2010-02-15T00:30-0600')
        assert_equal(np.datetime_as_string(b, timezone=tz('US/Eastern')),
                     '2010-02-15T01:30-0500')
        assert_equal(np.datetime_as_string(b, timezone=tz('US/Pacific')),
                     '2010-02-14T22:30-0800')

        # Dates to strings with a timezone attached is disabled by default
        assert_raises(TypeError, np.datetime_as_string, a, unit='D',
                           timezone=tz('US/Pacific'))
        # Check that we can print out the date in the specified time zone
        assert_equal(np.datetime_as_string(a, unit='D',
                           timezone=tz('US/Pacific'), casting='unsafe'),
                     '2010-03-14')
        assert_equal(np.datetime_as_string(b, unit='D',
                           timezone=tz('US/Central'), casting='unsafe'),
                     '2010-02-15')

    def test_datetime_arange(self):
        # With two datetimes provided as strings
        a = np.arange('2010-01-05', '2010-01-10', dtype='M8[D]')
        assert_equal(a.dtype, np.dtype('M8[D]'))
        assert_equal(a,
            np.array(['2010-01-05', '2010-01-06', '2010-01-07',
                      '2010-01-08', '2010-01-09'], dtype='M8[D]'))

        a = np.arange('1950-02-10', '1950-02-06', -1, dtype='M8[D]')
        assert_equal(a.dtype, np.dtype('M8[D]'))
        assert_equal(a,
            np.array(['1950-02-10', '1950-02-09', '1950-02-08',
                      '1950-02-07'], dtype='M8[D]'))

        # Unit should be detected as months here
        a = np.arange('1969-05', '1970-05', 2, dtype='M8')
        assert_equal(a.dtype, np.dtype('M8[M]'))
        assert_equal(a,
            np.datetime64('1969-05') + np.arange(12, step=2))

        # datetime, integer|timedelta works as well
        # produces arange (start, start + stop) in this case
        a = np.arange('1969', 18, 3, dtype='M8')
        assert_equal(a.dtype, np.dtype('M8[Y]'))
        assert_equal(a,
            np.datetime64('1969') + np.arange(18, step=3))
        a = np.arange('1969-12-19', 22, np.timedelta64(2), dtype='M8')
        assert_equal(a.dtype, np.dtype('M8[D]'))
        assert_equal(a,
            np.datetime64('1969-12-19') + np.arange(22, step=2))

        # Step of 0 is disallowed
        assert_raises(ValueError, np.arange, np.datetime64('today'),
                                np.datetime64('today') + 3, 0)
        # Promotion across nonlinear unit boundaries is disallowed
        assert_raises(TypeError, np.arange, np.datetime64('2011-03-01', 'D'),
                                np.timedelta64(5, 'M'))
        assert_raises(TypeError, np.arange,
                                np.datetime64('2012-02-03T14', 's'),
                                np.timedelta64(5, 'Y'))

    def test_datetime_arange_no_dtype(self):
        d = np.array('2010-01-04', dtype="M8[D]")
        assert_equal(np.arange(d, d + 1), d)
        assert_raises(ValueError, np.arange, d)

    def test_timedelta_arange(self):
        a = np.arange(3, 10, dtype='m8')
        assert_equal(a.dtype, np.dtype('m8'))
        assert_equal(a, np.timedelta64(0) + np.arange(3, 10))

        a = np.arange(np.timedelta64(3, 's'), 10, 2, dtype='m8')
        assert_equal(a.dtype, np.dtype('m8[s]'))
        assert_equal(a, np.timedelta64(0, 's') + np.arange(3, 10, 2))

        # Step of 0 is disallowed
        assert_raises(ValueError, np.arange, np.timedelta64(0),
                                np.timedelta64(5), 0)
        # Promotion across nonlinear unit boundaries is disallowed
        assert_raises(TypeError, np.arange, np.timedelta64(0, 'D'),
                                np.timedelta64(5, 'M'))
        assert_raises(TypeError, np.arange, np.timedelta64(0, 'Y'),
                                np.timedelta64(5, 'D'))

    def test_timedelta_arange_no_dtype(self):
        d = np.array(5, dtype="m8[D]")
        assert_equal(np.arange(d, d + 1), d)
        assert_raises(ValueError, np.arange, d)

    def test_datetime_maximum_reduce(self):
        a = np.array(['2010-01-02', '1999-03-14', '1833-03'], dtype='M8[D]')
        assert_equal(np.maximum.reduce(a).dtype, np.dtype('M8[D]'))
        assert_equal(np.maximum.reduce(a),
                     np.datetime64('2010-01-02'))

        a = np.array([1, 4, 0, 7, 2], dtype='m8[s]')
        assert_equal(np.maximum.reduce(a).dtype, np.dtype('m8[s]'))
        assert_equal(np.maximum.reduce(a),
                     np.timedelta64(7, 's'))

    def test_datetime_busday_offset(self):
        # First Monday in June
        assert_equal(
            np.busday_offset('2011-06', 0, roll='forward', weekmask='Mon'),
            np.datetime64('2011-06-06'))
        # Last Monday in June
        assert_equal(
            np.busday_offset('2011-07', -1, roll='forward', weekmask='Mon'),
            np.datetime64('2011-06-27'))
        assert_equal(
            np.busday_offset('2011-07', -1, roll='forward', weekmask='Mon'),
            np.datetime64('2011-06-27'))

        # Default M-F business days, different roll modes
        assert_equal(np.busday_offset('2010-08', 0, roll='backward'),
                     np.datetime64('2010-07-30'))
        assert_equal(np.busday_offset('2010-08', 0, roll='preceding'),
                     np.datetime64('2010-07-30'))
        assert_equal(np.busday_offset('2010-08', 0, roll='modifiedpreceding'),
                     np.datetime64('2010-08-02'))
        assert_equal(np.busday_offset('2010-08', 0, roll='modifiedfollowing'),
                     np.datetime64('2010-08-02'))
        assert_equal(np.busday_offset('2010-08', 0, roll='forward'),
                     np.datetime64('2010-08-02'))
        assert_equal(np.busday_offset('2010-08', 0, roll='following'),
                     np.datetime64('2010-08-02'))
        assert_equal(np.busday_offset('2010-10-30', 0, roll='following'),
                     np.datetime64('2010-11-01'))
        assert_equal(
                np.busday_offset('2010-10-30', 0, roll='modifiedfollowing'),
                np.datetime64('2010-10-29'))
        assert_equal(
                np.busday_offset('2010-10-30', 0, roll='modifiedpreceding'),
                np.datetime64('2010-10-29'))
        assert_equal(
                np.busday_offset('2010-10-16', 0, roll='modifiedfollowing'),
                np.datetime64('2010-10-18'))
        assert_equal(
                np.busday_offset('2010-10-16', 0, roll='modifiedpreceding'),
                np.datetime64('2010-10-15'))
        # roll='raise' by default
        assert_raises(ValueError, np.busday_offset, '2011-06-04', 0)

        # Bigger offset values
        assert_equal(np.busday_offset('2006-02-01', 25),
                     np.datetime64('2006-03-08'))
        assert_equal(np.busday_offset('2006-03-08', -25),
                     np.datetime64('2006-02-01'))
        assert_equal(np.busday_offset('2007-02-25', 11, weekmask='SatSun'),
                     np.datetime64('2007-04-07'))
        assert_equal(np.busday_offset('2007-04-07', -11, weekmask='SatSun'),
                     np.datetime64('2007-02-25'))

        # NaT values when roll is not raise
        assert_equal(np.busday_offset(np.datetime64('NaT'), 1, roll='nat'),
                     np.datetime64('NaT'))
        assert_equal(np.busday_offset(np.datetime64('NaT'), 1, roll='following'),
                     np.datetime64('NaT'))
        assert_equal(np.busday_offset(np.datetime64('NaT'), 1, roll='preceding'),
                     np.datetime64('NaT'))


    def test_datetime_busdaycalendar(self):
        # Check that it removes NaT, duplicates, and weekends
        # and sorts the result.
        bdd = np.busdaycalendar(
            holidays=['NaT', '2011-01-17', '2011-03-06', 'NaT',
                       '2011-12-26', '2011-05-30', '2011-01-17'])
        assert_equal(bdd.holidays,
            np.array(['2011-01-17', '2011-05-30', '2011-12-26'], dtype='M8'))
        # Default M-F weekmask
        assert_equal(bdd.weekmask, np.array([1, 1, 1, 1, 1, 0, 0], dtype='?'))

        # Check string weekmask with varying whitespace.
        bdd = np.busdaycalendar(weekmask="Sun TueWed  Thu\tFri")
        assert_equal(bdd.weekmask, np.array([0, 1, 1, 1, 1, 0, 1], dtype='?'))

        # Check length 7 0/1 string
        bdd = np.busdaycalendar(weekmask="0011001")
        assert_equal(bdd.weekmask, np.array([0, 0, 1, 1, 0, 0, 1], dtype='?'))

        # Check length 7 string weekmask.
        bdd = np.busdaycalendar(weekmask="Mon Tue")
        assert_equal(bdd.weekmask, np.array([1, 1, 0, 0, 0, 0, 0], dtype='?'))

        # All-zeros weekmask should raise
        assert_raises(ValueError, np.busdaycalendar, weekmask=[0, 0, 0, 0, 0, 0, 0])
        # weekday names must be correct case
        assert_raises(ValueError, np.busdaycalendar, weekmask="satsun")
        # All-zeros weekmask should raise
        assert_raises(ValueError, np.busdaycalendar, weekmask="")
        # Invalid weekday name codes should raise
        assert_raises(ValueError, np.busdaycalendar, weekmask="Mon Tue We")
        assert_raises(ValueError, np.busdaycalendar, weekmask="Max")
        assert_raises(ValueError, np.busdaycalendar, weekmask="Monday Tue")

    def test_datetime_busday_holidays_offset(self):
        # With exactly one holiday
        assert_equal(
            np.busday_offset('2011-11-10', 1, holidays=['2011-11-11']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-04', 5, holidays=['2011-11-11']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-10', 5, holidays=['2011-11-11']),
            np.datetime64('2011-11-18'))
        assert_equal(
            np.busday_offset('2011-11-14', -1, holidays=['2011-11-11']),
            np.datetime64('2011-11-10'))
        assert_equal(
            np.busday_offset('2011-11-18', -5, holidays=['2011-11-11']),
            np.datetime64('2011-11-10'))
        assert_equal(
            np.busday_offset('2011-11-14', -5, holidays=['2011-11-11']),
            np.datetime64('2011-11-04'))
        # With the holiday appearing twice
        assert_equal(
            np.busday_offset('2011-11-10', 1,
                holidays=['2011-11-11', '2011-11-11']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-14', -1,
                holidays=['2011-11-11', '2011-11-11']),
            np.datetime64('2011-11-10'))
        # With a NaT holiday
        assert_equal(
            np.busday_offset('2011-11-10', 1,
                holidays=['2011-11-11', 'NaT']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-14', -1,
                holidays=['NaT', '2011-11-11']),
            np.datetime64('2011-11-10'))
        # With another holiday after
        assert_equal(
            np.busday_offset('2011-11-10', 1,
                holidays=['2011-11-11', '2011-11-24']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-14', -1,
                holidays=['2011-11-11', '2011-11-24']),
            np.datetime64('2011-11-10'))
        # With another holiday before
        assert_equal(
            np.busday_offset('2011-11-10', 1,
                holidays=['2011-10-10', '2011-11-11']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-14', -1,
                holidays=['2011-10-10', '2011-11-11']),
            np.datetime64('2011-11-10'))
        # With another holiday before and after
        assert_equal(
            np.busday_offset('2011-11-10', 1,
                holidays=['2011-10-10', '2011-11-11', '2011-11-24']),
            np.datetime64('2011-11-14'))
        assert_equal(
            np.busday_offset('2011-11-14', -1,
                holidays=['2011-10-10', '2011-11-11', '2011-11-24']),
            np.datetime64('2011-11-10'))

        # A bigger forward jump across more than one week/holiday
        holidays = ['2011-10-10', '2011-11-11', '2011-11-24',
                  '2011-12-25', '2011-05-30', '2011-02-21',
                  '2011-12-26', '2012-01-02']
        bdd = np.busdaycalendar(weekmask='1111100', holidays=holidays)
        assert_equal(
            np.busday_offset('2011-10-03', 4, holidays=holidays),
            np.busday_offset('2011-10-03', 4))
        assert_equal(
            np.busday_offset('2011-10-03', 5, holidays=holidays),
            np.busday_offset('2011-10-03', 5 + 1))
        assert_equal(
            np.busday_offset('2011-10-03', 27, holidays=holidays),
            np.busday_offset('2011-10-03', 27 + 1))
        assert_equal(
            np.busday_offset('2011-10-03', 28, holidays=holidays),
            np.busday_offset('2011-10-03', 28 + 2))
        assert_equal(
            np.busday_offset('2011-10-03', 35, holidays=holidays),
            np.busday_offset('2011-10-03', 35 + 2))
        assert_equal(
            np.busday_offset('2011-10-03', 36, holidays=holidays),
            np.busday_offset('2011-10-03', 36 + 3))
        assert_equal(
            np.busday_offset('2011-10-03', 56, holidays=holidays),
            np.busday_offset('2011-10-03', 56 + 3))
        assert_equal(
            np.busday_offset('2011-10-03', 57, holidays=holidays),
            np.busday_offset('2011-10-03', 57 + 4))
        assert_equal(
            np.busday_offset('2011-10-03', 60, holidays=holidays),
            np.busday_offset('2011-10-03', 60 + 4))
        assert_equal(
            np.busday_offset('2011-10-03', 61, holidays=holidays),
            np.busday_offset('2011-10-03', 61 + 5))
        assert_equal(
            np.busday_offset('2011-10-03', 61, busdaycal=bdd),
            np.busday_offset('2011-10-03', 61 + 5))
        # A bigger backward jump across more than one week/holiday
        assert_equal(
            np.busday_offset('2012-01-03', -1, holidays=holidays),
            np.busday_offset('2012-01-03', -1 - 1))
        assert_equal(
            np.busday_offset('2012-01-03', -4, holidays=holidays),
            np.busday_offset('2012-01-03', -4 - 1))
        assert_equal(
            np.busday_offset('2012-01-03', -5, holidays=holidays),
            np.busday_offset('2012-01-03', -5 - 2))
        assert_equal(
            np.busday_offset('2012-01-03', -25, holidays=holidays),
            np.busday_offset('2012-01-03', -25 - 2))
        assert_equal(
            np.busday_offset('2012-01-03', -26, holidays=holidays),
            np.busday_offset('2012-01-03', -26 - 3))
        assert_equal(
            np.busday_offset('2012-01-03', -33, holidays=holidays),
            np.busday_offset('2012-01-03', -33 - 3))
        assert_equal(
            np.busday_offset('2012-01-03', -34, holidays=holidays),
            np.busday_offset('2012-01-03', -34 - 4))
        assert_equal(
            np.busday_offset('2012-01-03', -56, holidays=holidays),
            np.busday_offset('2012-01-03', -56 - 4))
        assert_equal(
            np.busday_offset('2012-01-03', -57, holidays=holidays),
            np.busday_offset('2012-01-03', -57 - 5))
        assert_equal(
            np.busday_offset('2012-01-03', -57, busdaycal=bdd),
            np.busday_offset('2012-01-03', -57 - 5))

        # Can't supply both a weekmask/holidays and busdaycal
        assert_raises(ValueError, np.busday_offset, '2012-01-03', -15,
                        weekmask='1111100', busdaycal=bdd)
        assert_raises(ValueError, np.busday_offset, '2012-01-03', -15,
                        holidays=holidays, busdaycal=bdd)

        # Roll with the holidays
        assert_equal(
            np.busday_offset('2011-12-25', 0,
                roll='forward', holidays=holidays),
            np.datetime64('2011-12-27'))
        assert_equal(
            np.busday_offset('2011-12-26', 0,
                roll='forward', holidays=holidays),
            np.datetime64('2011-12-27'))
        assert_equal(
            np.busday_offset('2011-12-26', 0,
                roll='backward', holidays=holidays),
            np.datetime64('2011-12-23'))
        assert_equal(
            np.busday_offset('2012-02-27', 0,
                roll='modifiedfollowing',
                holidays=['2012-02-27', '2012-02-26', '2012-02-28',
                          '2012-03-01', '2012-02-29']),
            np.datetime64('2012-02-24'))
        assert_equal(
            np.busday_offset('2012-03-06', 0,
                roll='modifiedpreceding',
                holidays=['2012-03-02', '2012-03-03', '2012-03-01',
                          '2012-03-05', '2012-03-07', '2012-03-06']),
            np.datetime64('2012-03-08'))

    def test_datetime_busday_holidays_count(self):
        holidays = ['2011-01-01', '2011-10-10', '2011-11-11', '2011-11-24',
                    '2011-12-25', '2011-05-30', '2011-02-21', '2011-01-17',
                    '2011-12-26', '2012-01-02', '2011-02-21', '2011-05-30',
                    '2011-07-01', '2011-07-04', '2011-09-05', '2011-10-10']
        bdd = np.busdaycalendar(weekmask='1111100', holidays=holidays)

        # Validate against busday_offset broadcast against
        # a range of offsets
        dates = np.busday_offset('2011-01-01', np.arange(366),
                        roll='forward', busdaycal=bdd)
        assert_equal(np.busday_count('2011-01-01', dates, busdaycal=bdd),
                     np.arange(366))
        # Returns negative value when reversed
        assert_equal(np.busday_count(dates, '2011-01-01', busdaycal=bdd),
                     -np.arange(366))

        dates = np.busday_offset('2011-12-31', -np.arange(366),
                        roll='forward', busdaycal=bdd)
        assert_equal(np.busday_count(dates, '2011-12-31', busdaycal=bdd),
                     np.arange(366))
        # Returns negative value when reversed
        assert_equal(np.busday_count('2011-12-31', dates, busdaycal=bdd),
                     -np.arange(366))

        # Can't supply both a weekmask/holidays and busdaycal
        assert_raises(ValueError, np.busday_offset, '2012-01-03', '2012-02-03',
                        weekmask='1111100', busdaycal=bdd)
        assert_raises(ValueError, np.busday_offset, '2012-01-03', '2012-02-03',
                        holidays=holidays, busdaycal=bdd)

        # Number of Mondays in March 2011
        assert_equal(np.busday_count('2011-03', '2011-04', weekmask='Mon'), 4)
        # Returns negative value when reversed
        assert_equal(np.busday_count('2011-04', '2011-03', weekmask='Mon'), -4)

    def test_datetime_is_busday(self):
        holidays = ['2011-01-01', '2011-10-10', '2011-11-11', '2011-11-24',
                    '2011-12-25', '2011-05-30', '2011-02-21', '2011-01-17',
                    '2011-12-26', '2012-01-02', '2011-02-21', '2011-05-30',
                    '2011-07-01', '2011-07-04', '2011-09-05', '2011-10-10',
                    'NaT']
        bdd = np.busdaycalendar(weekmask='1111100', holidays=holidays)

        # Weekend/weekday tests
        assert_equal(np.is_busday('2011-01-01'), False)
        assert_equal(np.is_busday('2011-01-02'), False)
        assert_equal(np.is_busday('2011-01-03'), True)

        # All the holidays are not business days
        assert_equal(np.is_busday(holidays, busdaycal=bdd),
                     np.zeros(len(holidays), dtype='?'))

    def test_datetime_y2038(self):
        # Test parsing on either side of the Y2038 boundary
        a = np.datetime64('2038-01-19T03:14:07')
        assert_equal(a.view(np.int64), 2**31 - 1)
        a = np.datetime64('2038-01-19T03:14:08')
        assert_equal(a.view(np.int64), 2**31)

        # Test parsing on either side of the Y2038 boundary with
        # a manually specified timezone offset
        with assert_warns(DeprecationWarning):
            a = np.datetime64('2038-01-19T04:14:07+0100')
            assert_equal(a.view(np.int64), 2**31 - 1)
        with assert_warns(DeprecationWarning):
            a = np.datetime64('2038-01-19T04:14:08+0100')
            assert_equal(a.view(np.int64), 2**31)

        # Test parsing a date after Y2038
        a = np.datetime64('2038-01-20T13:21:14')
        assert_equal(str(a), '2038-01-20T13:21:14')

class TestDateTimeData(TestCase):

    def test_basic(self):
        a = np.array(['1980-03-23'], dtype=np.datetime64)
        assert_equal(np.datetime_data(a.dtype), ('D', 1))

if __name__ == "__main__":
    run_module_suite()
