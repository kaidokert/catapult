from __future__ import division, absolute_import, print_function

import numpy.polynomial as poly
from numpy.testing import TestCase, run_module_suite, assert_


class test_str(TestCase):
    def test_polynomial_str(self):
        res = str(poly.Polynomial([0, 1]))
        tgt = 'poly([0., 1.])'
        assert_(res, tgt)

    def test_chebyshev_str(self):
        res = str(poly.Chebyshev([0, 1]))
        tgt = 'leg([0., 1.])'
        assert_(res, tgt)

    def test_legendre_str(self):
        res = str(poly.Legendre([0, 1]))
        tgt = 'leg([0., 1.])'
        assert_(res, tgt)

    def test_hermite_str(self):
        res = str(poly.Hermite([0, 1]))
        tgt = 'herm([0., 1.])'
        assert_(res, tgt)

    def test_hermiteE_str(self):
        res = str(poly.HermiteE([0, 1]))
        tgt = 'herme([0., 1.])'
        assert_(res, tgt)

    def test_laguerre_str(self):
        res = str(poly.Laguerre([0, 1]))
        tgt = 'lag([0., 1.])'
        assert_(res, tgt)


class test_repr(TestCase):
    def test_polynomial_str(self):
        res = repr(poly.Polynomial([0, 1]))
        tgt = 'Polynomial([0., 1.])'
        assert_(res, tgt)

    def test_chebyshev_str(self):
        res = repr(poly.Chebyshev([0, 1]))
        tgt = 'Chebyshev([0., 1.], [-1., 1.], [-1., 1.])'
        assert_(res, tgt)

    def test_legendre_repr(self):
        res = repr(poly.Legendre([0, 1]))
        tgt = 'Legendre([0., 1.], [-1., 1.], [-1., 1.])'
        assert_(res, tgt)

    def test_hermite_repr(self):
        res = repr(poly.Hermite([0, 1]))
        tgt = 'Hermite([0., 1.], [-1., 1.], [-1., 1.])'
        assert_(res, tgt)

    def test_hermiteE_repr(self):
        res = repr(poly.HermiteE([0, 1]))
        tgt = 'HermiteE([0., 1.], [-1., 1.], [-1., 1.])'
        assert_(res, tgt)

    def test_laguerre_repr(self):
        res = repr(poly.Laguerre([0, 1]))
        tgt = 'Laguerre([0., 1.], [0., 1.], [0., 1.])'
        assert_(res, tgt)


#

if __name__ == "__main__":
    run_module_suite()
