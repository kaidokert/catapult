from __future__ import division, absolute_import, print_function

from functools import reduce

import numpy as np
import numpy.core.umath as umath
import numpy.core.fromnumeric as fromnumeric
from numpy.testing import TestCase, run_module_suite, assert_
from numpy.ma.testutils import assert_array_equal
from numpy.ma import (
    MaskType, MaskedArray, absolute, add, all, allclose, allequal, alltrue,
    arange, arccos, arcsin, arctan, arctan2, array, average, choose,
    concatenate, conjugate, cos, cosh, count, divide, equal, exp, filled,
    getmask, greater, greater_equal, inner, isMaskedArray, less,
    less_equal, log, log10, make_mask, masked, masked_array, masked_equal,
    masked_greater, masked_greater_equal, masked_inside, masked_less,
    masked_less_equal, masked_not_equal, masked_outside,
    masked_print_option, masked_values, masked_where, maximum, minimum,
    multiply, nomask, nonzero, not_equal, ones, outer, product, put, ravel,
    repeat, resize, shape, sin, sinh, sometrue, sort, sqrt, subtract, sum,
    take, tan, tanh, transpose, where, zeros,
    )

pi = np.pi


def eq(v, w, msg=''):
    result = allclose(v, w)
    if not result:
        print("Not eq:%s\n%s\n----%s" % (msg, str(v), str(w)))
    return result


class TestMa(TestCase):

    def setUp(self):
        x = np.array([1., 1., 1., -2., pi/2.0, 4., 5., -10., 10., 1., 2., 3.])
        y = np.array([5., 0., 3., 2., -1., -4., 0., -10., 10., 1., 0., 3.])
        a10 = 10.
        m1 = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        m2 = [0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1]
        xm = array(x, mask=m1)
        ym = array(y, mask=m2)
        z = np.array([-.5, 0., .5, .8])
        zm = array(z, mask=[0, 1, 0, 0])
        xf = np.where(m1, 1e+20, x)
        s = x.shape
        xm.set_fill_value(1e+20)
        self.d = (x, y, a10, m1, m2, xm, ym, z, zm, xf, s)

    def test_testBasic1d(self):
        # Test of basic array creation and properties in 1 dimension.
        (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
        self.assertFalse(isMaskedArray(x))
        self.assertTrue(isMaskedArray(xm))
        self.assertEqual(shape(xm), s)
        self.assertEqual(xm.shape, s)
        self.assertEqual(xm.dtype, x.dtype)
        self.assertEqual(xm.size, reduce(lambda x, y:x * y, s))
        self.assertEqual(count(xm), len(m1) - reduce(lambda x, y:x + y, m1))
        self.assertTrue(eq(xm, xf))
        self.assertTrue(eq(filled(xm, 1.e20), xf))
        self.assertTrue(eq(x, xm))

    def test_testBasic2d(self):
        # Test of basic array creation and properties in 2 dimensions.
        for s in [(4, 3), (6, 2)]:
            (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
            x.shape = s
            y.shape = s
            xm.shape = s
            ym.shape = s
            xf.shape = s

            self.assertFalse(isMaskedArray(x))
            self.assertTrue(isMaskedArray(xm))
            self.assertEqual(shape(xm), s)
            self.assertEqual(xm.shape, s)
            self.assertEqual(xm.size, reduce(lambda x, y:x * y, s))
            self.assertEqual(count(xm),
                             len(m1) - reduce(lambda x, y:x + y, m1))
            self.assertTrue(eq(xm, xf))
            self.assertTrue(eq(filled(xm, 1.e20), xf))
            self.assertTrue(eq(x, xm))
            self.setUp()

    def test_testArithmetic(self):
        # Test of basic arithmetic.
        (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
        a2d = array([[1, 2], [0, 4]])
        a2dm = masked_array(a2d, [[0, 0], [1, 0]])
        self.assertTrue(eq(a2d * a2d, a2d * a2dm))
        self.assertTrue(eq(a2d + a2d, a2d + a2dm))
        self.assertTrue(eq(a2d - a2d, a2d - a2dm))
        for s in [(12,), (4, 3), (2, 6)]:
            x = x.reshape(s)
            y = y.reshape(s)
            xm = xm.reshape(s)
            ym = ym.reshape(s)
            xf = xf.reshape(s)
            self.assertTrue(eq(-x, -xm))
            self.assertTrue(eq(x + y, xm + ym))
            self.assertTrue(eq(x - y, xm - ym))
            self.assertTrue(eq(x * y, xm * ym))
            with np.errstate(divide='ignore', invalid='ignore'):
                self.assertTrue(eq(x / y, xm / ym))
            self.assertTrue(eq(a10 + y, a10 + ym))
            self.assertTrue(eq(a10 - y, a10 - ym))
            self.assertTrue(eq(a10 * y, a10 * ym))
            with np.errstate(divide='ignore', invalid='ignore'):
                self.assertTrue(eq(a10 / y, a10 / ym))
            self.assertTrue(eq(x + a10, xm + a10))
            self.assertTrue(eq(x - a10, xm - a10))
            self.assertTrue(eq(x * a10, xm * a10))
            self.assertTrue(eq(x / a10, xm / a10))
            self.assertTrue(eq(x ** 2, xm ** 2))
            self.assertTrue(eq(abs(x) ** 2.5, abs(xm) ** 2.5))
            self.assertTrue(eq(x ** y, xm ** ym))
            self.assertTrue(eq(np.add(x, y), add(xm, ym)))
            self.assertTrue(eq(np.subtract(x, y), subtract(xm, ym)))
            self.assertTrue(eq(np.multiply(x, y), multiply(xm, ym)))
            with np.errstate(divide='ignore', invalid='ignore'):
                self.assertTrue(eq(np.divide(x, y), divide(xm, ym)))

    def test_testMixedArithmetic(self):
        na = np.array([1])
        ma = array([1])
        self.assertTrue(isinstance(na + ma, MaskedArray))
        self.assertTrue(isinstance(ma + na, MaskedArray))

    def test_testUfuncs1(self):
        # Test various functions such as sin, cos.
        (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
        self.assertTrue(eq(np.cos(x), cos(xm)))
        self.assertTrue(eq(np.cosh(x), cosh(xm)))
        self.assertTrue(eq(np.sin(x), sin(xm)))
        self.assertTrue(eq(np.sinh(x), sinh(xm)))
        self.assertTrue(eq(np.tan(x), tan(xm)))
        self.assertTrue(eq(np.tanh(x), tanh(xm)))
        with np.errstate(divide='ignore', invalid='ignore'):
            self.assertTrue(eq(np.sqrt(abs(x)), sqrt(xm)))
            self.assertTrue(eq(np.log(abs(x)), log(xm)))
            self.assertTrue(eq(np.log10(abs(x)), log10(xm)))
        self.assertTrue(eq(np.exp(x), exp(xm)))
        self.assertTrue(eq(np.arcsin(z), arcsin(zm)))
        self.assertTrue(eq(np.arccos(z), arccos(zm)))
        self.assertTrue(eq(np.arctan(z), arctan(zm)))
        self.assertTrue(eq(np.arctan2(x, y), arctan2(xm, ym)))
        self.assertTrue(eq(np.absolute(x), absolute(xm)))
        self.assertTrue(eq(np.equal(x, y), equal(xm, ym)))
        self.assertTrue(eq(np.not_equal(x, y), not_equal(xm, ym)))
        self.assertTrue(eq(np.less(x, y), less(xm, ym)))
        self.assertTrue(eq(np.greater(x, y), greater(xm, ym)))
        self.assertTrue(eq(np.less_equal(x, y), less_equal(xm, ym)))
        self.assertTrue(eq(np.greater_equal(x, y), greater_equal(xm, ym)))
        self.assertTrue(eq(np.conjugate(x), conjugate(xm)))
        self.assertTrue(eq(np.concatenate((x, y)), concatenate((xm, ym))))
        self.assertTrue(eq(np.concatenate((x, y)), concatenate((x, y))))
        self.assertTrue(eq(np.concatenate((x, y)), concatenate((xm, y))))
        self.assertTrue(eq(np.concatenate((x, y, x)), concatenate((x, ym, x))))

    def test_xtestCount(self):
        # Test count
        ott = array([0., 1., 2., 3.], mask=[1, 0, 0, 0])
        self.assertTrue(count(ott).dtype.type is np.intp)
        self.assertEqual(3, count(ott))
        self.assertEqual(1, count(1))
        self.assertTrue(eq(0, array(1, mask=[1])))
        ott = ott.reshape((2, 2))
        self.assertTrue(count(ott).dtype.type is np.intp)
        assert_(isinstance(count(ott, 0), np.ndarray))
        self.assertTrue(count(ott).dtype.type is np.intp)
        self.assertTrue(eq(3, count(ott)))
        assert_(getmask(count(ott, 0)) is nomask)
        self.assertTrue(eq([1, 2], count(ott, 0)))

    def test_testMinMax(self):
        # Test minimum and maximum.
        (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
        xr = np.ravel(x)  # max doesn't work if shaped
        xmr = ravel(xm)

        # true because of careful selection of data
        self.assertTrue(eq(max(xr), maximum(xmr)))
        self.assertTrue(eq(min(xr), minimum(xmr)))

    def test_testAddSumProd(self):
        # Test add, sum, product.
        (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
        self.assertTrue(eq(np.add.reduce(x), add.reduce(x)))
        self.assertTrue(eq(np.add.accumulate(x), add.accumulate(x)))
        self.assertTrue(eq(4, sum(array(4), axis=0)))
        self.assertTrue(eq(4, sum(array(4), axis=0)))
        self.assertTrue(eq(np.sum(x, axis=0), sum(x, axis=0)))
        self.assertTrue(eq(np.sum(filled(xm, 0), axis=0), sum(xm, axis=0)))
        self.assertTrue(eq(np.sum(x, 0), sum(x, 0)))
        self.assertTrue(eq(np.product(x, axis=0), product(x, axis=0)))
        self.assertTrue(eq(np.product(x, 0), product(x, 0)))
        self.assertTrue(eq(np.product(filled(xm, 1), axis=0),
                           product(xm, axis=0)))
        if len(s) > 1:
            self.assertTrue(eq(np.concatenate((x, y), 1),
                               concatenate((xm, ym), 1)))
            self.assertTrue(eq(np.add.reduce(x, 1), add.reduce(x, 1)))
            self.assertTrue(eq(np.sum(x, 1), sum(x, 1)))
            self.assertTrue(eq(np.product(x, 1), product(x, 1)))

    def test_testCI(self):
        # Test of conversions and indexing
        x1 = np.array([1, 2, 4, 3])
        x2 = array(x1, mask=[1, 0, 0, 0])
        x3 = array(x1, mask=[0, 1, 0, 1])
        x4 = array(x1)
        # test conversion to strings
        str(x2)  # raises?
        repr(x2)  # raises?
        assert_(eq(np.sort(x1), sort(x2, fill_value=0)))
        # tests of indexing
        assert_(type(x2[1]) is type(x1[1]))
        assert_(x1[1] == x2[1])
        assert_(x2[0] is masked)
        assert_(eq(x1[2], x2[2]))
        assert_(eq(x1[2:5], x2[2:5]))
        assert_(eq(x1[:], x2[:]))
        assert_(eq(x1[1:], x3[1:]))
        x1[2] = 9
        x2[2] = 9
        assert_(eq(x1, x2))
        x1[1:3] = 99
        x2[1:3] = 99
        assert_(eq(x1, x2))
        x2[1] = masked
        assert_(eq(x1, x2))
        x2[1:3] = masked
        assert_(eq(x1, x2))
        x2[:] = x1
        x2[1] = masked
        assert_(allequal(getmask(x2), array([0, 1, 0, 0])))
        x3[:] = masked_array([1, 2, 3, 4], [0, 1, 1, 0])
        assert_(allequal(getmask(x3), array([0, 1, 1, 0])))
        x4[:] = masked_array([1, 2, 3, 4], [0, 1, 1, 0])
        assert_(allequal(getmask(x4), array([0, 1, 1, 0])))
        assert_(allequal(x4, array([1, 2, 3, 4])))
        x1 = np.arange(5) * 1.0
        x2 = masked_values(x1, 3.0)
        assert_(eq(x1, x2))
        assert_(allequal(array([0, 0, 0, 1, 0], MaskType), x2.mask))
        assert_(eq(3.0, x2.fill_value))
        x1 = array([1, 'hello', 2, 3], object)
        x2 = np.array([1, 'hello', 2, 3], object)
        s1 = x1[1]
        s2 = x2[1]
        self.assertEqual(type(s2), str)
        self.assertEqual(type(s1), str)
        self.assertEqual(s1, s2)
        assert_(x1[1:1].shape == (0,))

    def test_testCopySize(self):
        # Tests of some subtle points of copying and sizing.
        n = [0, 0, 1, 0, 0]
        m = make_mask(n)
        m2 = make_mask(m)
        self.assertTrue(m is m2)
        m3 = make_mask(m, copy=1)
        self.assertTrue(m is not m3)

        x1 = np.arange(5)
        y1 = array(x1, mask=m)
        self.assertTrue(y1._data is not x1)
        self.assertTrue(allequal(x1, y1._data))
        self.assertTrue(y1.mask is m)

        y1a = array(y1, copy=0)
        self.assertTrue(y1a.mask is y1.mask)

        y2 = array(x1, mask=m, copy=0)
        self.assertTrue(y2.mask is m)
        self.assertTrue(y2[2] is masked)
        y2[2] = 9
        self.assertTrue(y2[2] is not masked)
        self.assertTrue(y2.mask is not m)
        self.assertTrue(allequal(y2.mask, 0))

        y3 = array(x1 * 1.0, mask=m)
        self.assertTrue(filled(y3).dtype is (x1 * 1.0).dtype)

        x4 = arange(4)
        x4[2] = masked
        y4 = resize(x4, (8,))
        self.assertTrue(eq(concatenate([x4, x4]), y4))
        self.assertTrue(eq(getmask(y4), [0, 0, 1, 0, 0, 0, 1, 0]))
        y5 = repeat(x4, (2, 2, 2, 2), axis=0)
        self.assertTrue(eq(y5, [0, 0, 1, 1, 2, 2, 3, 3]))
        y6 = repeat(x4, 2, axis=0)
        self.assertTrue(eq(y5, y6))

    def test_testPut(self):
        # Test of put
        d = arange(5)
        n = [0, 0, 0, 1, 1]
        m = make_mask(n)
        x = array(d, mask=m)
        self.assertTrue(x[3] is masked)
        self.assertTrue(x[4] is masked)
        x[[1, 4]] = [10, 40]
        self.assertTrue(x.mask is not m)
        self.assertTrue(x[3] is masked)
        self.assertTrue(x[4] is not masked)
        self.assertTrue(eq(x, [0, 10, 2, -1, 40]))

        x = array(d, mask=m)
        x.put([0, 1, 2], [-1, 100, 200])
        self.assertTrue(eq(x, [-1, 100, 200, 0, 0]))
        self.assertTrue(x[3] is masked)
        self.assertTrue(x[4] is masked)

    def test_testMaPut(self):
        (x, y, a10, m1, m2, xm, ym, z, zm, xf, s) = self.d
        m = [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1]
        i = np.nonzero(m)[0]
        put(ym, i, zm)
        assert_(all(take(ym, i, axis=0) == zm))

    def test_testOddFeatures(self):
        # Test of other odd features
        x = arange(20)
        x = x.reshape(4, 5)
        x.flat[5] = 12
        assert_(x[1, 0] == 12)
        z = x + 10j * x
        assert_(eq(z.real, x))
        assert_(eq(z.imag, 10 * x))
        assert_(eq((z * conjugate(z)).real, 101 * x * x))
        z.imag[...] = 0.0

        x = arange(10)
        x[3] = masked
        assert_(str(x[3]) == str(masked))
        c = x >= 8
        assert_(count(where(c, masked, masked)) == 0)
        assert_(shape(where(c, masked, masked)) == c.shape)
        z = where(c, x, masked)
        assert_(z.dtype is x.dtype)
        assert_(z[3] is masked)
        assert_(z[4] is masked)
        assert_(z[7] is masked)
        assert_(z[8] is not masked)
        assert_(z[9] is not masked)
        assert_(eq(x, z))
        z = where(c, masked, x)
        assert_(z.dtype is x.dtype)
        assert_(z[3] is masked)
        assert_(z[4] is not masked)
        assert_(z[7] is not masked)
        assert_(z[8] is masked)
        assert_(z[9] is masked)
        z = masked_where(c, x)
        assert_(z.dtype is x.dtype)
        assert_(z[3] is masked)
        assert_(z[4] is not masked)
        assert_(z[7] is not masked)
        assert_(z[8] is masked)
        assert_(z[9] is masked)
        assert_(eq(x, z))
        x = array([1., 2., 3., 4., 5.])
        c = array([1, 1, 1, 0, 0])
        x[2] = masked
        z = where(c, x, -x)
        assert_(eq(z, [1., 2., 0., -4., -5]))
        c[0] = masked
        z = where(c, x, -x)
        assert_(eq(z, [1., 2., 0., -4., -5]))
        assert_(z[0] is masked)
        assert_(z[1] is not masked)
        assert_(z[2] is masked)
        assert_(eq(masked_where(greater(x, 2), x), masked_greater(x, 2)))
        assert_(eq(masked_where(greater_equal(x, 2), x),
                   masked_greater_equal(x, 2)))
        assert_(eq(masked_where(less(x, 2), x), masked_less(x, 2)))
        assert_(eq(masked_where(less_equal(x, 2), x), masked_less_equal(x, 2)))
        assert_(eq(masked_where(not_equal(x, 2), x), masked_not_equal(x, 2)))
        assert_(eq(masked_where(equal(x, 2), x), masked_equal(x, 2)))
        assert_(eq(masked_where(not_equal(x, 2), x), masked_not_equal(x, 2)))
        assert_(eq(masked_inside(list(range(5)), 1, 3), [0, 199, 199, 199, 4]))
        assert_(eq(masked_outside(list(range(5)), 1, 3), [199, 1, 2, 3, 199]))
        assert_(eq(masked_inside(array(list(range(5)),
                                       mask=[1, 0, 0, 0, 0]), 1, 3).mask,
                   [1, 1, 1, 1, 0]))
        assert_(eq(masked_outside(array(list(range(5)),
                                        mask=[0, 1, 0, 0, 0]), 1, 3).mask,
                   [1, 1, 0, 0, 1]))
        assert_(eq(masked_equal(array(list(range(5)),
                                      mask=[1, 0, 0, 0, 0]), 2).mask,
                   [1, 0, 1, 0, 0]))
        assert_(eq(masked_not_equal(array([2, 2, 1, 2, 1],
                                          mask=[1, 0, 0, 0, 0]), 2).mask,
                   [1, 0, 1, 0, 1]))
        assert_(eq(masked_where([1, 1, 0, 0, 0], [1, 2, 3, 4, 5]),
                   [99, 99, 3, 4, 5]))
        atest = ones((10, 10, 10), dtype=np.float32)
        btest = zeros(atest.shape, MaskType)
        ctest = masked_where(btest, atest)
        assert_(eq(atest, ctest))
        z = choose(c, (-x, x))
        assert_(eq(z, [1., 2., 0., -4., -5]))
        assert_(z[0] is masked)
        assert_(z[1] is not masked)
        assert_(z[2] is masked)
        x = arange(6)
        x[5] = masked
        y = arange(6) * 10
        y[2] = masked
        c = array([1, 1, 1, 0, 0, 0], mask=[1, 0, 0, 0, 0, 0])
        cm = c.filled(1)
        z = where(c, x, y)
        zm = where(cm, x, y)
        assert_(eq(z, zm))
        assert_(getmask(zm) is nomask)
        assert_(eq(zm, [0, 1, 2, 30, 40, 50]))
        z = where(c, masked, 1)
        assert_(eq(z, [99, 99, 99, 1, 1, 1]))
        z = where(c, 1, masked)
        assert_(eq(z, [99, 1, 1, 99, 99, 99]))

    def test_testMinMax2(self):
        # Test of minumum, maximum.
        assert_(eq(minimum([1, 2, 3], [4, 0, 9]), [1, 0, 3]))
        assert_(eq(maximum([1, 2, 3], [4, 0, 9]), [4, 2, 9]))
        x = arange(5)
        y = arange(5) - 2
        x[3] = masked
        y[0] = masked
        assert_(eq(minimum(x, y), where(less(x, y), x, y)))
        assert_(eq(maximum(x, y), where(greater(x, y), x, y)))
        assert_(minimum(x) == 0)
        assert_(maximum(x) == 4)

    def test_testTakeTransposeInnerOuter(self):
        # Test of take, transpose, inner, outer products
        x = arange(24)
        y = np.arange(24)
        x[5:6] = masked
        x = x.reshape(2, 3, 4)
        y = y.reshape(2, 3, 4)
        assert_(eq(np.transpose(y, (2, 0, 1)), transpose(x, (2, 0, 1))))
        assert_(eq(np.take(y, (2, 0, 1), 1), take(x, (2, 0, 1), 1)))
        assert_(eq(np.inner(filled(x, 0), filled(y, 0)),
                   inner(x, y)))
        assert_(eq(np.outer(filled(x, 0), filled(y, 0)),
                   outer(x, y)))
        y = array(['abc', 1, 'def', 2, 3], object)
        y[2] = masked
        t = take(y, [0, 3, 4])
        assert_(t[0] == 'abc')
        assert_(t[1] == 2)
        assert_(t[2] == 3)

    def test_testInplace(self):
        # Test of inplace operations and rich comparisons
        y = arange(10)

        x = arange(10)
        xm = arange(10)
        xm[2] = masked
        x += 1
        assert_(eq(x, y + 1))
        xm += 1
        assert_(eq(x, y + 1))

        x = arange(10)
        xm = arange(10)
        xm[2] = masked
        x -= 1
        assert_(eq(x, y - 1))
        xm -= 1
        assert_(eq(xm, y - 1))

        x = arange(10) * 1.0
        xm = arange(10) * 1.0
        xm[2] = masked
        x *= 2.0
        assert_(eq(x, y * 2))
        xm *= 2.0
        assert_(eq(xm, y * 2))

        x = arange(10) * 2
        xm = arange(10)
        xm[2] = masked
        x //= 2
        assert_(eq(x, y))
        xm //= 2
        assert_(eq(x, y))

        x = arange(10) * 1.0
        xm = arange(10) * 1.0
        xm[2] = masked
        x /= 2.0
        assert_(eq(x, y / 2.0))
        xm /= arange(10)
        assert_(eq(xm, ones((10,))))

        x = arange(10).astype(np.float32)
        xm = arange(10)
        xm[2] = masked
        x += 1.
        assert_(eq(x, y + 1.))

    def test_testPickle(self):
        # Test of pickling
        import pickle
        x = arange(12)
        x[4:10:2] = masked
        x = x.reshape(4, 3)
        s = pickle.dumps(x)
        y = pickle.loads(s)
        assert_(eq(x, y))

    def test_testMasked(self):
        # Test of masked element
        xx = arange(6)
        xx[1] = masked
        self.assertTrue(str(masked) == '--')
        self.assertTrue(xx[1] is masked)
        self.assertEqual(filled(xx[1], 0), 0)

    def test_testAverage1(self):
        # Test of average.
        ott = array([0., 1., 2., 3.], mask=[1, 0, 0, 0])
        self.assertTrue(eq(2.0, average(ott, axis=0)))
        self.assertTrue(eq(2.0, average(ott, weights=[1., 1., 2., 1.])))
        result, wts = average(ott, weights=[1., 1., 2., 1.], returned=1)
        self.assertTrue(eq(2.0, result))
        self.assertTrue(wts == 4.0)
        ott[:] = masked
        self.assertTrue(average(ott, axis=0) is masked)
        ott = array([0., 1., 2., 3.], mask=[1, 0, 0, 0])
        ott = ott.reshape(2, 2)
        ott[:, 1] = masked
        self.assertTrue(eq(average(ott, axis=0), [2.0, 0.0]))
        self.assertTrue(average(ott, axis=1)[0] is masked)
        self.assertTrue(eq([2., 0.], average(ott, axis=0)))
        result, wts = average(ott, axis=0, returned=1)
        self.assertTrue(eq(wts, [1., 0.]))

    def test_testAverage2(self):
        # More tests of average.
        w1 = [0, 1, 1, 1, 1, 0]
        w2 = [[0, 1, 1, 1, 1, 0], [1, 0, 0, 0, 0, 1]]
        x = arange(6)
        self.assertTrue(allclose(average(x, axis=0), 2.5))
        self.assertTrue(allclose(average(x, axis=0, weights=w1), 2.5))
        y = array([arange(6), 2.0 * arange(6)])
        self.assertTrue(allclose(average(y, None),
                                 np.add.reduce(np.arange(6)) * 3. / 12.))
        self.assertTrue(allclose(average(y, axis=0), np.arange(6) * 3. / 2.))
        self.assertTrue(allclose(average(y, axis=1),
                                 [average(x, axis=0), average(x, axis=0)*2.0]))
        self.assertTrue(allclose(average(y, None, weights=w2), 20. / 6.))
        self.assertTrue(allclose(average(y, axis=0, weights=w2),
                                 [0., 1., 2., 3., 4., 10.]))
        self.assertTrue(allclose(average(y, axis=1),
                                 [average(x, axis=0), average(x, axis=0)*2.0]))
        m1 = zeros(6)
        m2 = [0, 0, 1, 1, 0, 0]
        m3 = [[0, 0, 1, 1, 0, 0], [0, 1, 1, 1, 1, 0]]
        m4 = ones(6)
        m5 = [0, 1, 1, 1, 1, 1]
        self.assertTrue(allclose(average(masked_array(x, m1), axis=0), 2.5))
        self.assertTrue(allclose(average(masked_array(x, m2), axis=0), 2.5))
        self.assertTrue(average(masked_array(x, m4), axis=0) is masked)
        self.assertEqual(average(masked_array(x, m5), axis=0), 0.0)
        self.assertEqual(count(average(masked_array(x, m4), axis=0)), 0)
        z = masked_array(y, m3)
        self.assertTrue(allclose(average(z, None), 20. / 6.))
        self.assertTrue(allclose(average(z, axis=0),
                                 [0., 1., 99., 99., 4.0, 7.5]))
        self.assertTrue(allclose(average(z, axis=1), [2.5, 5.0]))
        self.assertTrue(allclose(average(z, axis=0, weights=w2),
                                 [0., 1., 99., 99., 4.0, 10.0]))

        a = arange(6)
        b = arange(6) * 3
        r1, w1 = average([[a, b], [b, a]], axis=1, returned=1)
        self.assertEqual(shape(r1), shape(w1))
        self.assertEqual(r1.shape, w1.shape)
        r2, w2 = average(ones((2, 2, 3)), axis=0, weights=[3, 1], returned=1)
        self.assertEqual(shape(w2), shape(r2))
        r2, w2 = average(ones((2, 2, 3)), returned=1)
        self.assertEqual(shape(w2), shape(r2))
        r2, w2 = average(ones((2, 2, 3)), weights=ones((2, 2, 3)), returned=1)
        self.assertTrue(shape(w2) == shape(r2))
        a2d = array([[1, 2], [0, 4]], float)
        a2dm = masked_array(a2d, [[0, 0], [1, 0]])
        a2da = average(a2d, axis=0)
        self.assertTrue(eq(a2da, [0.5, 3.0]))
        a2dma = average(a2dm, axis=0)
        self.assertTrue(eq(a2dma, [1.0, 3.0]))
        a2dma = average(a2dm, axis=None)
        self.assertTrue(eq(a2dma, 7. / 3.))
        a2dma = average(a2dm, axis=1)
        self.assertTrue(eq(a2dma, [1.5, 4.0]))

    def test_testToPython(self):
        self.assertEqual(1, int(array(1)))
        self.assertEqual(1.0, float(array(1)))
        self.assertEqual(1, int(array([[[1]]])))
        self.assertEqual(1.0, float(array([[1]])))
        self.assertRaises(TypeError, float, array([1, 1]))
        self.assertRaises(ValueError, bool, array([0, 1]))
        self.assertRaises(ValueError, bool, array([0, 0], mask=[0, 1]))

    def test_testScalarArithmetic(self):
        xm = array(0, mask=1)
        #TODO FIXME: Find out what the following raises a warning in r8247
        with np.errstate(divide='ignore'):
            self.assertTrue((1 / array(0)).mask)
        self.assertTrue((1 + xm).mask)
        self.assertTrue((-xm).mask)
        self.assertTrue((-xm).mask)
        self.assertTrue(maximum(xm, xm).mask)
        self.assertTrue(minimum(xm, xm).mask)
        self.assertTrue(xm.filled().dtype is xm._data.dtype)
        x = array(0, mask=0)
        self.assertTrue(x.filled() == x._data)
        self.assertEqual(str(xm), str(masked_print_option))

    def test_testArrayMethods(self):
        a = array([1, 3, 2])
        self.assertTrue(eq(a.any(), a._data.any()))
        self.assertTrue(eq(a.all(), a._data.all()))
        self.assertTrue(eq(a.argmax(), a._data.argmax()))
        self.assertTrue(eq(a.argmin(), a._data.argmin()))
        self.assertTrue(eq(a.choose(0, 1, 2, 3, 4),
                           a._data.choose(0, 1, 2, 3, 4)))
        self.assertTrue(eq(a.compress([1, 0, 1]), a._data.compress([1, 0, 1])))
        self.assertTrue(eq(a.conj(), a._data.conj()))
        self.assertTrue(eq(a.conjugate(), a._data.conjugate()))
        m = array([[1, 2], [3, 4]])
        self.assertTrue(eq(m.diagonal(), m._data.diagonal()))
        self.assertTrue(eq(a.sum(), a._data.sum()))
        self.assertTrue(eq(a.take([1, 2]), a._data.take([1, 2])))
        self.assertTrue(eq(m.transpose(), m._data.transpose()))

    def test_testArrayAttributes(self):
        a = array([1, 3, 2])
        self.assertEqual(a.ndim, 1)

    def test_testAPI(self):
        self.assertFalse([m for m in dir(np.ndarray)
                          if m not in dir(MaskedArray) and
                          not m.startswith('_')])

    def test_testSingleElementSubscript(self):
        a = array([1, 3, 2])
        b = array([1, 3, 2], mask=[1, 0, 1])
        self.assertEqual(a[0].shape, ())
        self.assertEqual(b[0].shape, ())
        self.assertEqual(b[1].shape, ())


class TestUfuncs(TestCase):
    def setUp(self):
        self.d = (array([1.0, 0, -1, pi / 2] * 2, mask=[0, 1] + [0] * 6),
                  array([1.0, 0, -1, pi / 2] * 2, mask=[1, 0] + [0] * 6),)

    def test_testUfuncRegression(self):
        f_invalid_ignore = [
            'sqrt', 'arctanh', 'arcsin', 'arccos',
            'arccosh', 'arctanh', 'log', 'log10', 'divide',
            'true_divide', 'floor_divide', 'remainder', 'fmod']
        for f in ['sqrt', 'log', 'log10', 'exp', 'conjugate',
                  'sin', 'cos', 'tan',
                  'arcsin', 'arccos', 'arctan',
                  'sinh', 'cosh', 'tanh',
                  'arcsinh',
                  'arccosh',
                  'arctanh',
                  'absolute', 'fabs', 'negative',
                  'floor', 'ceil',
                  'logical_not',
                  'add', 'subtract', 'multiply',
                  'divide', 'true_divide', 'floor_divide',
                  'remainder', 'fmod', 'hypot', 'arctan2',
                  'equal', 'not_equal', 'less_equal', 'greater_equal',
                  'less', 'greater',
                  'logical_and', 'logical_or', 'logical_xor']:
            try:
                uf = getattr(umath, f)
            except AttributeError:
                uf = getattr(fromnumeric, f)
            mf = getattr(np.ma, f)
            args = self.d[:uf.nin]
            with np.errstate():
                if f in f_invalid_ignore:
                    np.seterr(invalid='ignore')
                if f in ['arctanh', 'log', 'log10']:
                    np.seterr(divide='ignore')
                ur = uf(*args)
                mr = mf(*args)
            self.assertTrue(eq(ur.filled(0), mr.filled(0), f))
            self.assertTrue(eqmask(ur.mask, mr.mask))

    def test_reduce(self):
        a = self.d[0]
        self.assertFalse(alltrue(a, axis=0))
        self.assertTrue(sometrue(a, axis=0))
        self.assertEqual(sum(a[:3], axis=0), 0)
        self.assertEqual(product(a, axis=0), 0)

    def test_minmax(self):
        a = arange(1, 13).reshape(3, 4)
        amask = masked_where(a < 5, a)
        self.assertEqual(amask.max(), a.max())
        self.assertEqual(amask.min(), 5)
        self.assertTrue((amask.max(0) == a.max(0)).all())
        self.assertTrue((amask.min(0) == [5, 6, 7, 8]).all())
        self.assertTrue(amask.max(1)[0].mask)
        self.assertTrue(amask.min(1)[0].mask)

    def test_nonzero(self):
        for t in "?bhilqpBHILQPfdgFDGO":
            x = array([1, 0, 2, 0], mask=[0, 0, 1, 1])
            self.assertTrue(eq(nonzero(x), [0]))


class TestArrayMethods(TestCase):

    def setUp(self):
        x = np.array([8.375, 7.545, 8.828, 8.5, 1.757, 5.928,
                      8.43, 7.78, 9.865, 5.878, 8.979, 4.732,
                      3.012, 6.022, 5.095, 3.116, 5.238, 3.957,
                      6.04, 9.63, 7.712, 3.382, 4.489, 6.479,
                      7.189, 9.645, 5.395, 4.961, 9.894, 2.893,
                      7.357, 9.828, 6.272, 3.758, 6.693, 0.993])
        X = x.reshape(6, 6)
        XX = x.reshape(3, 2, 2, 3)

        m = np.array([0, 1, 0, 1, 0, 0,
                      1, 0, 1, 1, 0, 1,
                      0, 0, 0, 1, 0, 1,
                      0, 0, 0, 1, 1, 1,
                      1, 0, 0, 1, 0, 0,
                      0, 0, 1, 0, 1, 0])
        mx = array(data=x, mask=m)
        mX = array(data=X, mask=m.reshape(X.shape))
        mXX = array(data=XX, mask=m.reshape(XX.shape))

        self.d = (x, X, XX, m, mx, mX, mXX)

    def test_trace(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        mXdiag = mX.diagonal()
        self.assertEqual(mX.trace(), mX.diagonal().compressed().sum())
        self.assertTrue(eq(mX.trace(),
                           X.trace() - sum(mXdiag.mask * X.diagonal(),
                                           axis=0)))

    def test_clip(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        clipped = mx.clip(2, 8)
        self.assertTrue(eq(clipped.mask, mx.mask))
        self.assertTrue(eq(clipped._data, x.clip(2, 8)))
        self.assertTrue(eq(clipped._data, mx._data.clip(2, 8)))

    def test_ptp(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        (n, m) = X.shape
        self.assertEqual(mx.ptp(), mx.compressed().ptp())
        rows = np.zeros(n, np.float_)
        cols = np.zeros(m, np.float_)
        for k in range(m):
            cols[k] = mX[:, k].compressed().ptp()
        for k in range(n):
            rows[k] = mX[k].compressed().ptp()
        self.assertTrue(eq(mX.ptp(0), cols))
        self.assertTrue(eq(mX.ptp(1), rows))

    def test_swapaxes(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        mXswapped = mX.swapaxes(0, 1)
        self.assertTrue(eq(mXswapped[-1], mX[:, -1]))
        mXXswapped = mXX.swapaxes(0, 2)
        self.assertEqual(mXXswapped.shape, (2, 2, 3, 3))

    def test_cumprod(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        mXcp = mX.cumprod(0)
        self.assertTrue(eq(mXcp._data, mX.filled(1).cumprod(0)))
        mXcp = mX.cumprod(1)
        self.assertTrue(eq(mXcp._data, mX.filled(1).cumprod(1)))

    def test_cumsum(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        mXcp = mX.cumsum(0)
        self.assertTrue(eq(mXcp._data, mX.filled(0).cumsum(0)))
        mXcp = mX.cumsum(1)
        self.assertTrue(eq(mXcp._data, mX.filled(0).cumsum(1)))

    def test_varstd(self):
        (x, X, XX, m, mx, mX, mXX,) = self.d
        self.assertTrue(eq(mX.var(axis=None), mX.compressed().var()))
        self.assertTrue(eq(mX.std(axis=None), mX.compressed().std()))
        self.assertTrue(eq(mXX.var(axis=3).shape, XX.var(axis=3).shape))
        self.assertTrue(eq(mX.var().shape, X.var().shape))
        (mXvar0, mXvar1) = (mX.var(axis=0), mX.var(axis=1))
        for k in range(6):
            self.assertTrue(eq(mXvar1[k], mX[k].compressed().var()))
            self.assertTrue(eq(mXvar0[k], mX[:, k].compressed().var()))
            self.assertTrue(eq(np.sqrt(mXvar0[k]),
                               mX[:, k].compressed().std()))


def eqmask(m1, m2):
    if m1 is nomask:
        return m2 is nomask
    if m2 is nomask:
        return m1 is nomask
    return (m1 == m2).all()

if __name__ == "__main__":
    run_module_suite()
