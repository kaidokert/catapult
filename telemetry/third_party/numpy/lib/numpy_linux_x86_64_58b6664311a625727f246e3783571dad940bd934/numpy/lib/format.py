"""
Define a simple format for saving numpy arrays to disk with the full
information about them.

The ``.npy`` format is the standard binary file format in NumPy for
persisting a *single* arbitrary NumPy array on disk. The format stores all
of the shape and dtype information necessary to reconstruct the array
correctly even on another machine with a different architecture.
The format is designed to be as simple as possible while achieving
its limited goals.

The ``.npz`` format is the standard format for persisting *multiple* NumPy
arrays on disk. A ``.npz`` file is a zip file containing multiple ``.npy``
files, one for each array.

Capabilities
------------

- Can represent all NumPy arrays including nested record arrays and
  object arrays.

- Represents the data in its native binary form.

- Supports Fortran-contiguous arrays directly.

- Stores all of the necessary information to reconstruct the array
  including shape and dtype on a machine of a different
  architecture.  Both little-endian and big-endian arrays are
  supported, and a file with little-endian numbers will yield
  a little-endian array on any machine reading the file. The
  types are described in terms of their actual sizes. For example,
  if a machine with a 64-bit C "long int" writes out an array with
  "long ints", a reading machine with 32-bit C "long ints" will yield
  an array with 64-bit integers.

- Is straightforward to reverse engineer. Datasets often live longer than
  the programs that created them. A competent developer should be
  able to create a solution in their preferred programming language to
  read most ``.npy`` files that he has been given without much
  documentation.

- Allows memory-mapping of the data. See `open_memmep`.

- Can be read from a filelike stream object instead of an actual file.

- Stores object arrays, i.e. arrays containing elements that are arbitrary
  Python objects. Files with object arrays are not to be mmapable, but
  can be read and written to disk.

Limitations
-----------

- Arbitrary subclasses of numpy.ndarray are not completely preserved.
  Subclasses will be accepted for writing, but only the array data will
  be written out. A regular numpy.ndarray object will be created
  upon reading the file.

.. warning::

  Due to limitations in the interpretation of structured dtypes, dtypes
  with fields with empty names will have the names replaced by 'f0', 'f1',
  etc. Such arrays will not round-trip through the format entirely
  accurately. The data is intact; only the field names will differ. We are
  working on a fix for this. This fix will not require a change in the
  file format. The arrays with such structures can still be saved and
  restored, and the correct dtype may be restored by using the
  ``loadedarray.view(correct_dtype)`` method.

File extensions
---------------

We recommend using the ``.npy`` and ``.npz`` extensions for files saved
in this format. This is by no means a requirement; applications may wish
to use these file formats but use an extension specific to the
application. In the absence of an obvious alternative, however,
we suggest using ``.npy`` and ``.npz``.

Version numbering
-----------------

The version numbering of these formats is independent of NumPy version
numbering. If the format is upgraded, the code in `numpy.io` will still
be able to read and write Version 1.0 files.

Format Version 1.0
------------------

The first 6 bytes are a magic string: exactly ``\\x93NUMPY``.

The next 1 byte is an unsigned byte: the major version number of the file
format, e.g. ``\\x01``.

The next 1 byte is an unsigned byte: the minor version number of the file
format, e.g. ``\\x00``. Note: the version of the file format is not tied
to the version of the numpy package.

The next 2 bytes form a little-endian unsigned short int: the length of
the header data HEADER_LEN.

The next HEADER_LEN bytes form the header data describing the array's
format. It is an ASCII string which contains a Python literal expression
of a dictionary. It is terminated by a newline (``\\n``) and padded with
spaces (``\\x20``) to make the total length of
``magic string + 4 + HEADER_LEN`` be evenly divisible by 16 for alignment
purposes.

The dictionary contains three keys:

    "descr" : dtype.descr
      An object that can be passed as an argument to the `numpy.dtype`
      constructor to create the array's dtype.
    "fortran_order" : bool
      Whether the array data is Fortran-contiguous or not. Since
      Fortran-contiguous arrays are a common form of non-C-contiguity,
      we allow them to be written directly to disk for efficiency.
    "shape" : tuple of int
      The shape of the array.

For repeatability and readability, the dictionary keys are sorted in
alphabetic order. This is for convenience only. A writer SHOULD implement
this if possible. A reader MUST NOT depend on this.

Following the header comes the array data. If the dtype contains Python
objects (i.e. ``dtype.hasobject is True``), then the data is a Python
pickle of the array. Otherwise the data is the contiguous (either C-
or Fortran-, depending on ``fortran_order``) bytes of the array.
Consumers can figure out the number of bytes by multiplying the number
of elements given by the shape (noting that ``shape=()`` means there is
1 element) by ``dtype.itemsize``.

Format Version 2.0
------------------

The version 1.0 format only allowed the array header to have a total size of
65535 bytes.  This can be exceeded by structured arrays with a large number of
columns.  The version 2.0 format extends the header size to 4 GiB.
`numpy.save` will automatically save in 2.0 format if the data requires it,
else it will always use the more compatible 1.0 format.

The description of the fourth element of the header therefore has become:
"The next 4 bytes form a little-endian unsigned int: the length of the header
data HEADER_LEN."

Notes
-----
The ``.npy`` format, including reasons for creating it and a comparison of
alternatives, is described fully in the "npy-format" NEP.

"""
from __future__ import division, absolute_import, print_function

import numpy
import sys
import io
import warnings
from numpy.lib.utils import safe_eval
from numpy.compat import asbytes, asstr, isfileobj, long, basestring

if sys.version_info[0] >= 3:
    import pickle
else:
    import cPickle as pickle

MAGIC_PREFIX = asbytes('\x93NUMPY')
MAGIC_LEN = len(MAGIC_PREFIX) + 2
BUFFER_SIZE = 2**18  # size of buffer for reading npz files in bytes

# difference between version 1.0 and 2.0 is a 4 byte (I) header length
# instead of 2 bytes (H) allowing storage of large structured arrays

def _check_version(version):
    if version not in [(1, 0), (2, 0), None]:
        msg = "we only support format version (1,0) and (2, 0), not %s"
        raise ValueError(msg % (version,))

def magic(major, minor):
    """ Return the magic string for the given file format version.

    Parameters
    ----------
    major : int in [0, 255]
    minor : int in [0, 255]

    Returns
    -------
    magic : str

    Raises
    ------
    ValueError if the version cannot be formatted.
    """
    if major < 0 or major > 255:
        raise ValueError("major version must be 0 <= major < 256")
    if minor < 0 or minor > 255:
        raise ValueError("minor version must be 0 <= minor < 256")
    if sys.version_info[0] < 3:
        return MAGIC_PREFIX + chr(major) + chr(minor)
    else:
        return MAGIC_PREFIX + bytes([major, minor])

def read_magic(fp):
    """ Read the magic string to get the version of the file format.

    Parameters
    ----------
    fp : filelike object

    Returns
    -------
    major : int
    minor : int
    """
    magic_str = _read_bytes(fp, MAGIC_LEN, "magic string")
    if magic_str[:-2] != MAGIC_PREFIX:
        msg = "the magic string is not correct; expected %r, got %r"
        raise ValueError(msg % (MAGIC_PREFIX, magic_str[:-2]))
    if sys.version_info[0] < 3:
        major, minor = map(ord, magic_str[-2:])
    else:
        major, minor = magic_str[-2:]
    return major, minor

def dtype_to_descr(dtype):
    """
    Get a serializable descriptor from the dtype.

    The .descr attribute of a dtype object cannot be round-tripped through
    the dtype() constructor. Simple types, like dtype('float32'), have
    a descr which looks like a record array with one field with '' as
    a name. The dtype() constructor interprets this as a request to give
    a default name.  Instead, we construct descriptor that can be passed to
    dtype().

    Parameters
    ----------
    dtype : dtype
        The dtype of the array that will be written to disk.

    Returns
    -------
    descr : object
        An object that can be passed to `numpy.dtype()` in order to
        replicate the input dtype.

    """
    if dtype.names is not None:
        # This is a record array. The .descr is fine.  XXX: parts of the
        # record array with an empty name, like padding bytes, still get
        # fiddled with. This needs to be fixed in the C implementation of
        # dtype().
        return dtype.descr
    else:
        return dtype.str

def header_data_from_array_1_0(array):
    """ Get the dictionary of header metadata from a numpy.ndarray.

    Parameters
    ----------
    array : numpy.ndarray

    Returns
    -------
    d : dict
        This has the appropriate entries for writing its string representation
        to the header of the file.
    """
    d = {'shape': array.shape}
    if array.flags.c_contiguous:
        d['fortran_order'] = False
    elif array.flags.f_contiguous:
        d['fortran_order'] = True
    else:
        # Totally non-contiguous data. We will have to make it C-contiguous
        # before writing. Note that we need to test for C_CONTIGUOUS first
        # because a 1-D array is both C_CONTIGUOUS and F_CONTIGUOUS.
        d['fortran_order'] = False

    d['descr'] = dtype_to_descr(array.dtype)
    return d

def _write_array_header(fp, d, version=None):
    """ Write the header for an array and returns the version used

    Parameters
    ----------
    fp : filelike object
    d : dict
        This has the appropriate entries for writing its string representation
        to the header of the file.
    version: tuple or None
        None means use oldest that works
        explicit version will raise a ValueError if the format does not
        allow saving this data.  Default: None
    Returns
    -------
    version : tuple of int
        the file version which needs to be used to store the data
    """
    import struct
    header = ["{"]
    for key, value in sorted(d.items()):
        # Need to use repr here, since we eval these when reading
        header.append("'%s': %s, " % (key, repr(value)))
    header.append("}")
    header = "".join(header)
    # Pad the header with spaces and a final newline such that the magic
    # string, the header-length short and the header are aligned on a
    # 16-byte boundary.  Hopefully, some system, possibly memory-mapping,
    # can take advantage of our premature optimization.
    current_header_len = MAGIC_LEN + 2 + len(header) + 1  # 1 for the newline
    topad = 16 - (current_header_len % 16)
    header = header + ' '*topad + '\n'
    header = asbytes(_filter_header(header))

    hlen = len(header)
    if hlen < 256*256 and version in (None, (1, 0)):
        version = (1, 0)
        header_prefix = magic(1, 0) + struct.pack('<H', hlen)
    elif hlen < 2**32 and version in (None, (2, 0)):
        version = (2, 0)
        header_prefix = magic(2, 0) + struct.pack('<I', hlen)
    else:
        msg = "Header length %s too big for version=%s"
        msg %= (hlen, version)
        raise ValueError(msg)

    fp.write(header_prefix)
    fp.write(header)
    return version

def write_array_header_1_0(fp, d):
    """ Write the header for an array using the 1.0 format.

    Parameters
    ----------
    fp : filelike object
    d : dict
        This has the appropriate entries for writing its string
        representation to the header of the file.
    """
    _write_array_header(fp, d, (1, 0))


def write_array_header_2_0(fp, d):
    """ Write the header for an array using the 2.0 format.
        The 2.0 format allows storing very large structured arrays.

    .. versionadded:: 1.9.0

    Parameters
    ----------
    fp : filelike object
    d : dict
        This has the appropriate entries for writing its string
        representation to the header of the file.
    """
    _write_array_header(fp, d, (2, 0))

def read_array_header_1_0(fp):
    """
    Read an array header from a filelike object using the 1.0 file format
    version.

    This will leave the file object located just after the header.

    Parameters
    ----------
    fp : filelike object
        A file object or something with a `.read()` method like a file.

    Returns
    -------
    shape : tuple of int
        The shape of the array.
    fortran_order : bool
        The array data will be written out directly if it is either
        C-contiguous or Fortran-contiguous. Otherwise, it will be made
        contiguous before writing it out.
    dtype : dtype
        The dtype of the file's data.

    Raises
    ------
    ValueError
        If the data is invalid.

    """
    return _read_array_header(fp, version=(1, 0))

def read_array_header_2_0(fp):
    """
    Read an array header from a filelike object using the 2.0 file format
    version.

    This will leave the file object located just after the header.

    .. versionadded:: 1.9.0

    Parameters
    ----------
    fp : filelike object
        A file object or something with a `.read()` method like a file.

    Returns
    -------
    shape : tuple of int
        The shape of the array.
    fortran_order : bool
        The array data will be written out directly if it is either
        C-contiguous or Fortran-contiguous. Otherwise, it will be made
        contiguous before writing it out.
    dtype : dtype
        The dtype of the file's data.

    Raises
    ------
    ValueError
        If the data is invalid.

    """
    return _read_array_header(fp, version=(2, 0))


def _filter_header(s):
    """Clean up 'L' in npz header ints.

    Cleans up the 'L' in strings representing integers. Needed to allow npz
    headers produced in Python2 to be read in Python3.

    Parameters
    ----------
    s : byte string
        Npy file header.

    Returns
    -------
    header : str
        Cleaned up header.

    """
    import tokenize
    if sys.version_info[0] >= 3:
        from io import StringIO
    else:
        from StringIO import StringIO

    tokens = []
    last_token_was_number = False
    for token in tokenize.generate_tokens(StringIO(asstr(s)).read):
        token_type = token[0]
        token_string = token[1]
        if (last_token_was_number and
                token_type == tokenize.NAME and
                token_string == "L"):
            continue
        else:
            tokens.append(token)
        last_token_was_number = (token_type == tokenize.NUMBER)
    return tokenize.untokenize(tokens)


def _read_array_header(fp, version):
    """
    see read_array_header_1_0
    """
    # Read an unsigned, little-endian short int which has the length of the
    # header.
    import struct
    if version == (1, 0):
        hlength_str = _read_bytes(fp, 2, "array header length")
        header_length = struct.unpack('<H', hlength_str)[0]
        header = _read_bytes(fp, header_length, "array header")
    elif version == (2, 0):
        hlength_str = _read_bytes(fp, 4, "array header length")
        header_length = struct.unpack('<I', hlength_str)[0]
        header = _read_bytes(fp, header_length, "array header")
    else:
        raise ValueError("Invalid version %r" % version)

    # The header is a pretty-printed string representation of a literal
    # Python dictionary with trailing newlines padded to a 16-byte
    # boundary. The keys are strings.
    #   "shape" : tuple of int
    #   "fortran_order" : bool
    #   "descr" : dtype.descr
    header = _filter_header(header)
    try:
        d = safe_eval(header)
    except SyntaxError as e:
        msg = "Cannot parse header: %r\nException: %r"
        raise ValueError(msg % (header, e))
    if not isinstance(d, dict):
        msg = "Header is not a dictionary: %r"
        raise ValueError(msg % d)
    keys = sorted(d.keys())
    if keys != ['descr', 'fortran_order', 'shape']:
        msg = "Header does not contain the correct keys: %r"
        raise ValueError(msg % (keys,))

    # Sanity-check the values.
    if (not isinstance(d['shape'], tuple) or
            not numpy.all([isinstance(x, (int, long)) for x in d['shape']])):
        msg = "shape is not valid: %r"
        raise ValueError(msg % (d['shape'],))
    if not isinstance(d['fortran_order'], bool):
        msg = "fortran_order is not a valid bool: %r"
        raise ValueError(msg % (d['fortran_order'],))
    try:
        dtype = numpy.dtype(d['descr'])
    except TypeError as e:
        msg = "descr is not a valid dtype descriptor: %r"
        raise ValueError(msg % (d['descr'],))

    return d['shape'], d['fortran_order'], dtype

def write_array(fp, array, version=None, allow_pickle=True, pickle_kwargs=None):
    """
    Write an array to an NPY file, including a header.

    If the array is neither C-contiguous nor Fortran-contiguous AND the
    file_like object is not a real file object, this function will have to
    copy data in memory.

    Parameters
    ----------
    fp : file_like object
        An open, writable file object, or similar object with a
        ``.write()`` method.
    array : ndarray
        The array to write to disk.
    version : (int, int) or None, optional
        The version number of the format. None means use the oldest
        supported version that is able to store the data.  Default: None
    allow_pickle : bool, optional
        Whether to allow writing pickled data. Default: True
    pickle_kwargs : dict, optional
        Additional keyword arguments to pass to pickle.dump, excluding
        'protocol'. These are only useful when pickling objects in object
        arrays on Python 3 to Python 2 compatible format.

    Raises
    ------
    ValueError
        If the array cannot be persisted. This includes the case of
        allow_pickle=False and array being an object array.
    Various other errors
        If the array contains Python objects as part of its dtype, the
        process of pickling them may raise various errors if the objects
        are not picklable.

    """
    _check_version(version)
    used_ver = _write_array_header(fp, header_data_from_array_1_0(array),
                                   version)
    # this warning can be removed when 1.9 has aged enough
    if version != (2, 0) and used_ver == (2, 0):
        warnings.warn("Stored array in format 2.0. It can only be"
                      "read by NumPy >= 1.9", UserWarning)

    # Set buffer size to 16 MiB to hide the Python loop overhead.
    buffersize = max(16 * 1024 ** 2 // array.itemsize, 1)

    if array.dtype.hasobject:
        # We contain Python objects so we cannot write out the data
        # directly.  Instead, we will pickle it out with version 2 of the
        # pickle protocol.
        if not allow_pickle:
            raise ValueError("Object arrays cannot be saved when "
                             "allow_pickle=False")
        if pickle_kwargs is None:
            pickle_kwargs = {}
        pickle.dump(array, fp, protocol=2, **pickle_kwargs)
    elif array.flags.f_contiguous and not array.flags.c_contiguous:
        if isfileobj(fp):
            array.T.tofile(fp)
        else:
            for chunk in numpy.nditer(
                    array, flags=['external_loop', 'buffered', 'zerosize_ok'],
                    buffersize=buffersize, order='F'):
                fp.write(chunk.tobytes('C'))
    else:
        if isfileobj(fp):
            array.tofile(fp)
        else:
            for chunk in numpy.nditer(
                    array, flags=['external_loop', 'buffered', 'zerosize_ok'],
                    buffersize=buffersize, order='C'):
                fp.write(chunk.tobytes('C'))


def read_array(fp, allow_pickle=True, pickle_kwargs=None):
    """
    Read an array from an NPY file.

    Parameters
    ----------
    fp : file_like object
        If this is not a real file object, then this may take extra memory
        and time.
    allow_pickle : bool, optional
        Whether to allow reading pickled data. Default: True
    pickle_kwargs : dict
        Additional keyword arguments to pass to pickle.load. These are only
        useful when loading object arrays saved on Python 2 when using
        Python 3.

    Returns
    -------
    array : ndarray
        The array from the data on disk.

    Raises
    ------
    ValueError
        If the data is invalid, or allow_pickle=False and the file contains
        an object array.

    """
    version = read_magic(fp)
    _check_version(version)
    shape, fortran_order, dtype = _read_array_header(fp, version)
    if len(shape) == 0:
        count = 1
    else:
        count = numpy.multiply.reduce(shape)

    # Now read the actual data.
    if dtype.hasobject:
        # The array contained Python objects. We need to unpickle the data.
        if not allow_pickle:
            raise ValueError("Object arrays cannot be loaded when "
                             "allow_pickle=False")
        if pickle_kwargs is None:
            pickle_kwargs = {}
        try:
            array = pickle.load(fp, **pickle_kwargs)
        except UnicodeError as err:
            if sys.version_info[0] >= 3:
                # Friendlier error message
                raise UnicodeError("Unpickling a python object failed: %r\n"
                                   "You may need to pass the encoding= option "
                                   "to numpy.load" % (err,))
            raise
    else:
        if isfileobj(fp):
            # We can use the fast fromfile() function.
            array = numpy.fromfile(fp, dtype=dtype, count=count)
        else:
            # This is not a real file. We have to read it the
            # memory-intensive way.
            # crc32 module fails on reads greater than 2 ** 32 bytes,
            # breaking large reads from gzip streams. Chunk reads to
            # BUFFER_SIZE bytes to avoid issue and reduce memory overhead
            # of the read. In non-chunked case count < max_read_count, so
            # only one read is performed.

            max_read_count = BUFFER_SIZE // min(BUFFER_SIZE, dtype.itemsize)

            array = numpy.empty(count, dtype=dtype)
            for i in range(0, count, max_read_count):
                read_count = min(max_read_count, count - i)
                read_size = int(read_count * dtype.itemsize)
                data = _read_bytes(fp, read_size, "array data")
                array[i:i+read_count] = numpy.frombuffer(data, dtype=dtype,
                                                         count=read_count)

        if fortran_order:
            array.shape = shape[::-1]
            array = array.transpose()
        else:
            array.shape = shape

    return array


def open_memmap(filename, mode='r+', dtype=None, shape=None,
                fortran_order=False, version=None):
    """
    Open a .npy file as a memory-mapped array.

    This may be used to read an existing file or create a new one.

    Parameters
    ----------
    filename : str
        The name of the file on disk.  This may *not* be a file-like
        object.
    mode : str, optional
        The mode in which to open the file; the default is 'r+'.  In
        addition to the standard file modes, 'c' is also accepted to mean
        "copy on write."  See `memmap` for the available mode strings.
    dtype : data-type, optional
        The data type of the array if we are creating a new file in "write"
        mode, if not, `dtype` is ignored.  The default value is None, which
        results in a data-type of `float64`.
    shape : tuple of int
        The shape of the array if we are creating a new file in "write"
        mode, in which case this parameter is required.  Otherwise, this
        parameter is ignored and is thus optional.
    fortran_order : bool, optional
        Whether the array should be Fortran-contiguous (True) or
        C-contiguous (False, the default) if we are creating a new file in
        "write" mode.
    version : tuple of int (major, minor) or None
        If the mode is a "write" mode, then this is the version of the file
        format used to create the file.  None means use the oldest
        supported version that is able to store the data.  Default: None

    Returns
    -------
    marray : memmap
        The memory-mapped array.

    Raises
    ------
    ValueError
        If the data or the mode is invalid.
    IOError
        If the file is not found or cannot be opened correctly.

    See Also
    --------
    memmap

    """
    if not isinstance(filename, basestring):
        raise ValueError("Filename must be a string.  Memmap cannot use"
                         " existing file handles.")

    if 'w' in mode:
        # We are creating the file, not reading it.
        # Check if we ought to create the file.
        _check_version(version)
        # Ensure that the given dtype is an authentic dtype object rather
        # than just something that can be interpreted as a dtype object.
        dtype = numpy.dtype(dtype)
        if dtype.hasobject:
            msg = "Array can't be memory-mapped: Python objects in dtype."
            raise ValueError(msg)
        d = dict(
            descr=dtype_to_descr(dtype),
            fortran_order=fortran_order,
            shape=shape,
        )
        # If we got here, then it should be safe to create the file.
        fp = open(filename, mode+'b')
        try:
            used_ver = _write_array_header(fp, d, version)
            # this warning can be removed when 1.9 has aged enough
            if version != (2, 0) and used_ver == (2, 0):
                warnings.warn("Stored array in format 2.0. It can only be"
                              "read by NumPy >= 1.9", UserWarning)
            offset = fp.tell()
        finally:
            fp.close()
    else:
        # Read the header of the file first.
        fp = open(filename, 'rb')
        try:
            version = read_magic(fp)
            _check_version(version)

            shape, fortran_order, dtype = _read_array_header(fp, version)
            if dtype.hasobject:
                msg = "Array can't be memory-mapped: Python objects in dtype."
                raise ValueError(msg)
            offset = fp.tell()
        finally:
            fp.close()

    if fortran_order:
        order = 'F'
    else:
        order = 'C'

    # We need to change a write-only mode to a read-write mode since we've
    # already written data to the file.
    if mode == 'w+':
        mode = 'r+'

    marray = numpy.memmap(filename, dtype=dtype, shape=shape, order=order,
        mode=mode, offset=offset)

    return marray


def _read_bytes(fp, size, error_template="ran out of data"):
    """
    Read from file-like object until size bytes are read.
    Raises ValueError if not EOF is encountered before size bytes are read.
    Non-blocking objects only supported if they derive from io objects.

    Required as e.g. ZipExtFile in python 2.6 can return less data than
    requested.
    """
    data = bytes()
    while True:
        # io files (default in python3) return None or raise on
        # would-block, python2 file will truncate, probably nothing can be
        # done about that.  note that regular files can't be non-blocking
        try:
            r = fp.read(size - len(data))
            data += r
            if len(r) == 0 or len(data) == size:
                break
        except io.BlockingIOError:
            pass
    if len(data) != size:
        msg = "EOF: reading %s, expected %d bytes got %d"
        raise ValueError(msg % (error_template, size, len(data)))
    else:
        return data
