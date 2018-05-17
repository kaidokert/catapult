from __future__ import division, absolute_import, print_function

import sys

import numpy as np
from numpy.compat import sixu
from numpy.testing import (
     run_module_suite, assert_, assert_equal, assert_array_equal,
     assert_raises
)

# Switch between new behaviour when NPY_RELAXED_STRIDES_CHECKING is set.
NPY_RELAXED_STRIDES_CHECKING = np.ones((10, 1), order='C').flags.f_contiguous


def test_array_array():
    tobj = type(object)
    ones11 = np.ones((1, 1), np.float64)
    tndarray = type(ones11)
    # Test is_ndarray
    assert_equal(np.array(ones11, dtype=np.float64), ones11)
    old_refcount = sys.getrefcount(tndarray)
    np.array(ones11)
    assert_equal(old_refcount, sys.getrefcount(tndarray))

    # test None
    assert_equal(np.array(None, dtype=np.float64),
                 np.array(np.nan, dtype=np.float64))
    old_refcount = sys.getrefcount(tobj)
    np.array(None, dtype=np.float64)
    assert_equal(old_refcount, sys.getrefcount(tobj))

    # test scalar
    assert_equal(np.array(1.0, dtype=np.float64),
                 np.ones((), dtype=np.float64))
    old_refcount = sys.getrefcount(np.float64)
    np.array(np.array(1.0, dtype=np.float64), dtype=np.float64)
    assert_equal(old_refcount, sys.getrefcount(np.float64))

    # test string
    S2 = np.dtype((str, 2))
    S3 = np.dtype((str, 3))
    S5 = np.dtype((str, 5))
    assert_equal(np.array("1.0", dtype=np.float64),
                 np.ones((), dtype=np.float64))
    assert_equal(np.array("1.0").dtype, S3)
    assert_equal(np.array("1.0", dtype=str).dtype, S3)
    assert_equal(np.array("1.0", dtype=S2), np.array("1."))
    assert_equal(np.array("1", dtype=S5), np.ones((), dtype=S5))

    # test unicode
    _unicode = globals().get("unicode")
    if _unicode:
        U2 = np.dtype((_unicode, 2))
        U3 = np.dtype((_unicode, 3))
        U5 = np.dtype((_unicode, 5))
        assert_equal(np.array(_unicode("1.0"), dtype=np.float64),
                     np.ones((), dtype=np.float64))
        assert_equal(np.array(_unicode("1.0")).dtype, U3)
        assert_equal(np.array(_unicode("1.0"), dtype=_unicode).dtype, U3)
        assert_equal(np.array(_unicode("1.0"), dtype=U2),
                     np.array(_unicode("1.")))
        assert_equal(np.array(_unicode("1"), dtype=U5),
                     np.ones((), dtype=U5))

    builtins = getattr(__builtins__, '__dict__', __builtins__)
    assert_(isinstance(builtins, dict))

    # test buffer
    _buffer = builtins.get("buffer")
    if _buffer and sys.version_info[:3] >= (2, 7, 5):
        # This test fails for earlier versions of Python.
        # Evidently a bug got fixed in 2.7.5.
        dat = np.array(_buffer('1.0'), dtype=np.float64)
        assert_equal(dat, [49.0, 46.0, 48.0])
        assert_(dat.dtype.type is np.float64)

        dat = np.array(_buffer(b'1.0'))
        assert_equal(dat, [49, 46, 48])
        assert_(dat.dtype.type is np.uint8)

    # test memoryview, new version of buffer
    _memoryview = builtins.get("memoryview")
    if _memoryview:
        dat = np.array(_memoryview(b'1.0'), dtype=np.float64)
        assert_equal(dat, [49.0, 46.0, 48.0])
        assert_(dat.dtype.type is np.float64)

        dat = np.array(_memoryview(b'1.0'))
        assert_equal(dat, [49, 46, 48])
        assert_(dat.dtype.type is np.uint8)

    # test array interface
    a = np.array(100.0, dtype=np.float64)
    o = type("o", (object,),
             dict(__array_interface__=a.__array_interface__))
    assert_equal(np.array(o, dtype=np.float64), a)

    # test array_struct interface
    a = np.array([(1, 4.0, 'Hello'), (2, 6.0, 'World')],
                 dtype=[('f0', int), ('f1', float), ('f2', str)])
    o = type("o", (object,),
             dict(__array_struct__=a.__array_struct__))
    ## wasn't what I expected... is np.array(o) supposed to equal a ?
    ## instead we get a array([...], dtype=">V18")
    assert_equal(str(np.array(o).data), str(a.data))

    # test array
    o = type("o", (object,),
             dict(__array__=lambda *x: np.array(100.0, dtype=np.float64)))()
    assert_equal(np.array(o, dtype=np.float64), np.array(100.0, np.float64))

    # test recursion
    nested = 1.5
    for i in range(np.MAXDIMS):
        nested = [nested]

    # no error
    np.array(nested)

    # Exceeds recursion limit
    assert_raises(ValueError, np.array, [nested], dtype=np.float64)

    # Try with lists...
    assert_equal(np.array([None] * 10, dtype=np.float64),
                 np.full((10,), np.nan, dtype=np.float64))
    assert_equal(np.array([[None]] * 10, dtype=np.float64),
                 np.full((10, 1), np.nan, dtype=np.float64))
    assert_equal(np.array([[None] * 10], dtype=np.float64),
                 np.full((1, 10), np.nan, dtype=np.float64))
    assert_equal(np.array([[None] * 10] * 10, dtype=np.float64),
                 np.full((10, 10), np.nan, dtype=np.float64))

    assert_equal(np.array([1.0] * 10, dtype=np.float64),
                 np.ones((10,), dtype=np.float64))
    assert_equal(np.array([[1.0]] * 10, dtype=np.float64),
                 np.ones((10, 1), dtype=np.float64))
    assert_equal(np.array([[1.0] * 10], dtype=np.float64),
                 np.ones((1, 10), dtype=np.float64))
    assert_equal(np.array([[1.0] * 10] * 10, dtype=np.float64),
                 np.ones((10, 10), dtype=np.float64))

    # Try with tuples
    assert_equal(np.array((None,) * 10, dtype=np.float64),
                 np.full((10,), np.nan, dtype=np.float64))
    assert_equal(np.array([(None,)] * 10, dtype=np.float64),
                 np.full((10, 1), np.nan, dtype=np.float64))
    assert_equal(np.array([(None,) * 10], dtype=np.float64),
                 np.full((1, 10), np.nan, dtype=np.float64))
    assert_equal(np.array([(None,) * 10] * 10, dtype=np.float64),
                 np.full((10, 10), np.nan, dtype=np.float64))

    assert_equal(np.array((1.0,) * 10, dtype=np.float64),
                 np.ones((10,), dtype=np.float64))
    assert_equal(np.array([(1.0,)] * 10, dtype=np.float64),
                 np.ones((10, 1), dtype=np.float64))
    assert_equal(np.array([(1.0,) * 10], dtype=np.float64),
                 np.ones((1, 10), dtype=np.float64))
    assert_equal(np.array([(1.0,) * 10] * 10, dtype=np.float64),
                 np.ones((10, 10), dtype=np.float64))


def test_fastCopyAndTranspose():
    # 0D array
    a = np.array(2)
    b = np.fastCopyAndTranspose(a)
    assert_equal(b, a.T)
    assert_(b.flags.owndata)

    # 1D array
    a = np.array([3, 2, 7, 0])
    b = np.fastCopyAndTranspose(a)
    assert_equal(b, a.T)
    assert_(b.flags.owndata)

    # 2D array
    a = np.arange(6).reshape(2, 3)
    b = np.fastCopyAndTranspose(a)
    assert_equal(b, a.T)
    assert_(b.flags.owndata)

def test_array_astype():
    a = np.arange(6, dtype='f4').reshape(2, 3)
    # Default behavior: allows unsafe casts, keeps memory layout,
    #                   always copies.
    b = a.astype('i4')
    assert_equal(a, b)
    assert_equal(b.dtype, np.dtype('i4'))
    assert_equal(a.strides, b.strides)
    b = a.T.astype('i4')
    assert_equal(a.T, b)
    assert_equal(b.dtype, np.dtype('i4'))
    assert_equal(a.T.strides, b.strides)
    b = a.astype('f4')
    assert_equal(a, b)
    assert_(not (a is b))

    # copy=False parameter can sometimes skip a copy
    b = a.astype('f4', copy=False)
    assert_(a is b)

    # order parameter allows overriding of the memory layout,
    # forcing a copy if the layout is wrong
    b = a.astype('f4', order='F', copy=False)
    assert_equal(a, b)
    assert_(not (a is b))
    assert_(b.flags.f_contiguous)

    b = a.astype('f4', order='C', copy=False)
    assert_equal(a, b)
    assert_(a is b)
    assert_(b.flags.c_contiguous)

    # casting parameter allows catching bad casts
    b = a.astype('c8', casting='safe')
    assert_equal(a, b)
    assert_equal(b.dtype, np.dtype('c8'))

    assert_raises(TypeError, a.astype, 'i4', casting='safe')

    # subok=False passes through a non-subclassed array
    b = a.astype('f4', subok=0, copy=False)
    assert_(a is b)

    a = np.matrix([[0, 1, 2], [3, 4, 5]], dtype='f4')

    # subok=True passes through a matrix
    b = a.astype('f4', subok=True, copy=False)
    assert_(a is b)

    # subok=True is default, and creates a subtype on a cast
    b = a.astype('i4', copy=False)
    assert_equal(a, b)
    assert_equal(type(b), np.matrix)

    # subok=False never returns a matrix
    b = a.astype('f4', subok=False, copy=False)
    assert_equal(a, b)
    assert_(not (a is b))
    assert_(type(b) is not np.matrix)

    # Make sure converting from string object to fixed length string
    # does not truncate.
    a = np.array([b'a'*100], dtype='O')
    b = a.astype('S')
    assert_equal(a, b)
    assert_equal(b.dtype, np.dtype('S100'))
    a = np.array([sixu('a')*100], dtype='O')
    b = a.astype('U')
    assert_equal(a, b)
    assert_equal(b.dtype, np.dtype('U100'))

    # Same test as above but for strings shorter than 64 characters
    a = np.array([b'a'*10], dtype='O')
    b = a.astype('S')
    assert_equal(a, b)
    assert_equal(b.dtype, np.dtype('S10'))
    a = np.array([sixu('a')*10], dtype='O')
    b = a.astype('U')
    assert_equal(a, b)
    assert_equal(b.dtype, np.dtype('U10'))

    a = np.array(123456789012345678901234567890, dtype='O').astype('S')
    assert_array_equal(a, np.array(b'1234567890' * 3, dtype='S30'))
    a = np.array(123456789012345678901234567890, dtype='O').astype('U')
    assert_array_equal(a, np.array(sixu('1234567890' * 3), dtype='U30'))

    a = np.array([123456789012345678901234567890], dtype='O').astype('S')
    assert_array_equal(a, np.array(b'1234567890' * 3, dtype='S30'))
    a = np.array([123456789012345678901234567890], dtype='O').astype('U')
    assert_array_equal(a, np.array(sixu('1234567890' * 3), dtype='U30'))

    a = np.array(123456789012345678901234567890, dtype='S')
    assert_array_equal(a, np.array(b'1234567890' * 3, dtype='S30'))
    a = np.array(123456789012345678901234567890, dtype='U')
    assert_array_equal(a, np.array(sixu('1234567890' * 3), dtype='U30'))

    a = np.array(sixu('a\u0140'), dtype='U')
    b = np.ndarray(buffer=a, dtype='uint32', shape=2)
    assert_(b.size == 2)

    a = np.array([1000], dtype='i4')
    assert_raises(TypeError, a.astype, 'S1', casting='safe')

    a = np.array(1000, dtype='i4')
    assert_raises(TypeError, a.astype, 'U1', casting='safe')

def test_copyto_fromscalar():
    a = np.arange(6, dtype='f4').reshape(2, 3)

    # Simple copy
    np.copyto(a, 1.5)
    assert_equal(a, 1.5)
    np.copyto(a.T, 2.5)
    assert_equal(a, 2.5)

    # Where-masked copy
    mask = np.array([[0, 1, 0], [0, 0, 1]], dtype='?')
    np.copyto(a, 3.5, where=mask)
    assert_equal(a, [[2.5, 3.5, 2.5], [2.5, 2.5, 3.5]])
    mask = np.array([[0, 1], [1, 1], [1, 0]], dtype='?')
    np.copyto(a.T, 4.5, where=mask)
    assert_equal(a, [[2.5, 4.5, 4.5], [4.5, 4.5, 3.5]])

def test_copyto():
    a = np.arange(6, dtype='i4').reshape(2, 3)

    # Simple copy
    np.copyto(a, [[3, 1, 5], [6, 2, 1]])
    assert_equal(a, [[3, 1, 5], [6, 2, 1]])

    # Overlapping copy should work
    np.copyto(a[:, :2], a[::-1, 1::-1])
    assert_equal(a, [[2, 6, 5], [1, 3, 1]])

    # Defaults to 'same_kind' casting
    assert_raises(TypeError, np.copyto, a, 1.5)

    # Force a copy with 'unsafe' casting, truncating 1.5 to 1
    np.copyto(a, 1.5, casting='unsafe')
    assert_equal(a, 1)

    # Copying with a mask
    np.copyto(a, 3, where=[True, False, True])
    assert_equal(a, [[3, 1, 3], [3, 1, 3]])

    # Casting rule still applies with a mask
    assert_raises(TypeError, np.copyto, a, 3.5, where=[True, False, True])

    # Lists of integer 0's and 1's is ok too
    np.copyto(a, 4.0, casting='unsafe', where=[[0, 1, 1], [1, 0, 0]])
    assert_equal(a, [[3, 4, 4], [4, 1, 3]])

    # Overlapping copy with mask should work
    np.copyto(a[:, :2], a[::-1, 1::-1], where=[[0, 1], [1, 1]])
    assert_equal(a, [[3, 4, 4], [4, 3, 3]])

    # 'dst' must be an array
    assert_raises(TypeError, np.copyto, [1, 2, 3], [2, 3, 4])

def test_copyto_permut():
    # test explicit overflow case
    pad = 500
    l = [True] * pad + [True, True, True, True]
    r = np.zeros(len(l)-pad)
    d = np.ones(len(l)-pad)
    mask = np.array(l)[pad:]
    np.copyto(r, d, where=mask[::-1])

    # test all permutation of possible masks, 9 should be sufficient for
    # current 4 byte unrolled code
    power = 9
    d = np.ones(power)
    for i in range(2**power):
        r = np.zeros(power)
        l = [(i & x) != 0 for x in range(power)]
        mask = np.array(l)
        np.copyto(r, d, where=mask)
        assert_array_equal(r == 1, l)
        assert_equal(r.sum(), sum(l))

        r = np.zeros(power)
        np.copyto(r, d, where=mask[::-1])
        assert_array_equal(r == 1, l[::-1])
        assert_equal(r.sum(), sum(l))

        r = np.zeros(power)
        np.copyto(r[::2], d[::2], where=mask[::2])
        assert_array_equal(r[::2] == 1, l[::2])
        assert_equal(r[::2].sum(), sum(l[::2]))

        r = np.zeros(power)
        np.copyto(r[::2], d[::2], where=mask[::-2])
        assert_array_equal(r[::2] == 1, l[::-2])
        assert_equal(r[::2].sum(), sum(l[::-2]))

        for c in [0xFF, 0x7F, 0x02, 0x10]:
            r = np.zeros(power)
            mask = np.array(l)
            imask = np.array(l).view(np.uint8)
            imask[mask != 0] = c
            np.copyto(r, d, where=mask)
            assert_array_equal(r == 1, l)
            assert_equal(r.sum(), sum(l))

    r = np.zeros(power)
    np.copyto(r, d, where=True)
    assert_equal(r.sum(), r.size)
    r = np.ones(power)
    d = np.zeros(power)
    np.copyto(r, d, where=False)
    assert_equal(r.sum(), r.size)

def test_copy_order():
    a = np.arange(24).reshape(2, 1, 3, 4)
    b = a.copy(order='F')
    c = np.arange(24).reshape(2, 1, 4, 3).swapaxes(2, 3)

    def check_copy_result(x, y, ccontig, fcontig, strides=False):
        assert_(not (x is y))
        assert_equal(x, y)
        assert_equal(res.flags.c_contiguous, ccontig)
        assert_equal(res.flags.f_contiguous, fcontig)
        # This check is impossible only because
        # NPY_RELAXED_STRIDES_CHECKING changes the strides actively
        if not NPY_RELAXED_STRIDES_CHECKING:
            if strides:
                assert_equal(x.strides, y.strides)
            else:
                assert_(x.strides != y.strides)

    # Validate the initial state of a, b, and c
    assert_(a.flags.c_contiguous)
    assert_(not a.flags.f_contiguous)
    assert_(not b.flags.c_contiguous)
    assert_(b.flags.f_contiguous)
    assert_(not c.flags.c_contiguous)
    assert_(not c.flags.f_contiguous)

    # Copy with order='C'
    res = a.copy(order='C')
    check_copy_result(res, a, ccontig=True, fcontig=False, strides=True)
    res = b.copy(order='C')
    check_copy_result(res, b, ccontig=True, fcontig=False, strides=False)
    res = c.copy(order='C')
    check_copy_result(res, c, ccontig=True, fcontig=False, strides=False)
    res = np.copy(a, order='C')
    check_copy_result(res, a, ccontig=True, fcontig=False, strides=True)
    res = np.copy(b, order='C')
    check_copy_result(res, b, ccontig=True, fcontig=False, strides=False)
    res = np.copy(c, order='C')
    check_copy_result(res, c, ccontig=True, fcontig=False, strides=False)

    # Copy with order='F'
    res = a.copy(order='F')
    check_copy_result(res, a, ccontig=False, fcontig=True, strides=False)
    res = b.copy(order='F')
    check_copy_result(res, b, ccontig=False, fcontig=True, strides=True)
    res = c.copy(order='F')
    check_copy_result(res, c, ccontig=False, fcontig=True, strides=False)
    res = np.copy(a, order='F')
    check_copy_result(res, a, ccontig=False, fcontig=True, strides=False)
    res = np.copy(b, order='F')
    check_copy_result(res, b, ccontig=False, fcontig=True, strides=True)
    res = np.copy(c, order='F')
    check_copy_result(res, c, ccontig=False, fcontig=True, strides=False)

    # Copy with order='K'
    res = a.copy(order='K')
    check_copy_result(res, a, ccontig=True, fcontig=False, strides=True)
    res = b.copy(order='K')
    check_copy_result(res, b, ccontig=False, fcontig=True, strides=True)
    res = c.copy(order='K')
    check_copy_result(res, c, ccontig=False, fcontig=False, strides=True)
    res = np.copy(a, order='K')
    check_copy_result(res, a, ccontig=True, fcontig=False, strides=True)
    res = np.copy(b, order='K')
    check_copy_result(res, b, ccontig=False, fcontig=True, strides=True)
    res = np.copy(c, order='K')
    check_copy_result(res, c, ccontig=False, fcontig=False, strides=True)

def test_contiguous_flags():
    a = np.ones((4, 4, 1))[::2,:,:]
    if NPY_RELAXED_STRIDES_CHECKING:
        a.strides = a.strides[:2] + (-123,)
    b = np.ones((2, 2, 1, 2, 2)).swapaxes(3, 4)

    def check_contig(a, ccontig, fcontig):
        assert_(a.flags.c_contiguous == ccontig)
        assert_(a.flags.f_contiguous == fcontig)

    # Check if new arrays are correct:
    check_contig(a, False, False)
    check_contig(b, False, False)
    if NPY_RELAXED_STRIDES_CHECKING:
        check_contig(np.empty((2, 2, 0, 2, 2)), True, True)
        check_contig(np.array([[[1], [2]]], order='F'), True, True)
    else:
        check_contig(np.empty((2, 2, 0, 2, 2)), True, False)
        check_contig(np.array([[[1], [2]]], order='F'), False, True)
    check_contig(np.empty((2, 2)), True, False)
    check_contig(np.empty((2, 2), order='F'), False, True)

    # Check that np.array creates correct contiguous flags:
    check_contig(np.array(a, copy=False), False, False)
    check_contig(np.array(a, copy=False, order='C'), True, False)
    check_contig(np.array(a, ndmin=4, copy=False, order='F'), False, True)

    if NPY_RELAXED_STRIDES_CHECKING:
        # Check slicing update of flags and :
        check_contig(a[0], True, True)
        check_contig(a[None, ::4, ..., None], True, True)
        check_contig(b[0, 0, ...], False, True)
        check_contig(b[:,:, 0:0,:,:], True, True)
    else:
        # Check slicing update of flags:
        check_contig(a[0], True, False)
        # Would be nice if this was C-Contiguous:
        check_contig(a[None, 0, ..., None], False, False)
        check_contig(b[0, 0, 0, ...], False, True)

    # Test ravel and squeeze.
    check_contig(a.ravel(), True, True)
    check_contig(np.ones((1, 3, 1)).squeeze(), True, True)

def test_broadcast_arrays():
    # Test user defined dtypes
    a = np.array([(1, 2, 3)], dtype='u4,u4,u4')
    b = np.array([(1, 2, 3), (4, 5, 6), (7, 8, 9)], dtype='u4,u4,u4')
    result = np.broadcast_arrays(a, b)
    assert_equal(result[0], np.array([(1, 2, 3), (1, 2, 3), (1, 2, 3)], dtype='u4,u4,u4'))
    assert_equal(result[1], np.array([(1, 2, 3), (4, 5, 6), (7, 8, 9)], dtype='u4,u4,u4'))

if __name__ == "__main__":
    run_module_suite()
