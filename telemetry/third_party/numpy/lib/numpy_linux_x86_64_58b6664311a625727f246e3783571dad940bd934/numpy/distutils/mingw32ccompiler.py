"""
Support code for building Python extensions on Windows.

    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support)
    # 3. Force windows to use g77

"""
from __future__ import division, absolute_import, print_function

import os
import sys
import subprocess
import re

# Overwrite certain distutils.ccompiler functions:
import numpy.distutils.ccompiler

if sys.version_info[0] < 3:
    from . import log
else:
    from numpy.distutils import log
# NT stuff
# 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
# 2. Force windows to use gcc (we're struggling with MSVC and g77 support)
#    --> this is done in numpy/distutils/ccompiler.py
# 3. Force windows to use g77

import distutils.cygwinccompiler
from distutils.version import StrictVersion
from numpy.distutils.ccompiler import gen_preprocess_options, gen_lib_options
from distutils.unixccompiler import UnixCCompiler
from distutils.msvccompiler import get_build_version as get_build_msvc_version
from distutils.errors import (DistutilsExecError, CompileError,
                              UnknownFileError)
from numpy.distutils.misc_util import (msvc_runtime_library,
                                       get_build_architecture)

# Useful to generate table of symbols from a dll
_START = re.compile(r'\[Ordinal/Name Pointer\] Table')
_TABLE = re.compile(r'^\s+\[([\s*[0-9]*)\] ([a-zA-Z0-9_]*)')

# the same as cygwin plus some additional parameters
class Mingw32CCompiler(distutils.cygwinccompiler.CygwinCCompiler):
    """ A modified MingW32 compiler compatible with an MSVC built Python.

    """

    compiler_type = 'mingw32'

    def __init__ (self,
                  verbose=0,
                  dry_run=0,
                  force=0):

        distutils.cygwinccompiler.CygwinCCompiler.__init__ (self, verbose,
                                                            dry_run, force)

        # we need to support 3.2 which doesn't match the standard
        # get_versions methods regex
        if self.gcc_version is None:
            import re
            p = subprocess.Popen(['gcc', '-dumpversion'], shell=True,
                                 stdout=subprocess.PIPE)
            out_string = p.stdout.read()
            p.stdout.close()
            result = re.search('(\d+\.\d+)', out_string)
            if result:
                self.gcc_version = StrictVersion(result.group(1))

        # A real mingw32 doesn't need to specify a different entry point,
        # but cygwin 2.91.57 in no-cygwin-mode needs it.
        if self.gcc_version <= "2.91.57":
            entry_point = '--entry _DllMain@12'
        else:
            entry_point = ''

        if self.linker_dll == 'dllwrap':
            # Commented out '--driver-name g++' part that fixes weird
            #   g++.exe: g++: No such file or directory
            # error (mingw 1.0 in Enthon24 tree, gcc-3.4.5).
            # If the --driver-name part is required for some environment
            # then make the inclusion of this part specific to that
            # environment.
            self.linker = 'dllwrap' #  --driver-name g++'
        elif self.linker_dll == 'gcc':
            self.linker = 'g++'

        # **changes: eric jones 4/11/01
        # 1. Check for import library on Windows.  Build if it doesn't exist.

        build_import_library()

        # Check for custom msvc runtime library on Windows. Build if it doesn't exist.
        msvcr_success = build_msvcr_library()
        msvcr_dbg_success = build_msvcr_library(debug=True)
        if msvcr_success or msvcr_dbg_success:
            # add preprocessor statement for using customized msvcr lib
            self.define_macro('NPY_MINGW_USE_CUSTOM_MSVCR')

        # Define the MSVC version as hint for MinGW
        msvcr_version = '0x%03i0' % int(msvc_runtime_library().lstrip('msvcr'))
        self.define_macro('__MSVCRT_VERSION__', msvcr_version)

        # MS_WIN64 should be defined when building for amd64 on windows,
        # but python headers define it only for MS compilers, which has all
        # kind of bad consequences, like using Py_ModuleInit4 instead of
        # Py_ModuleInit4_64, etc... So we add it here
        if get_build_architecture() == 'AMD64':
            if self.gcc_version < "4.0":
                self.set_executables(
                    compiler='gcc -g -DDEBUG -DMS_WIN64 -mno-cygwin -O0 -Wall',
                    compiler_so='gcc -g -DDEBUG -DMS_WIN64 -mno-cygwin -O0'
                                ' -Wall -Wstrict-prototypes',
                    linker_exe='gcc -g -mno-cygwin',
                    linker_so='gcc -g -mno-cygwin -shared')
            else:
                # gcc-4 series releases do not support -mno-cygwin option
                self.set_executables(
                    compiler='gcc -g -DDEBUG -DMS_WIN64 -O0 -Wall',
                    compiler_so='gcc -g -DDEBUG -DMS_WIN64 -O0 -Wall -Wstrict-prototypes',
                    linker_exe='gcc -g',
                    linker_so='gcc -g -shared')
        else:
            if self.gcc_version <= "3.0.0":
                self.set_executables(
                    compiler='gcc -mno-cygwin -O2 -w',
                    compiler_so='gcc -mno-cygwin -mdll -O2 -w'
                                ' -Wstrict-prototypes',
                    linker_exe='g++ -mno-cygwin',
                    linker_so='%s -mno-cygwin -mdll -static %s' %
                              (self.linker, entry_point))
            elif self.gcc_version < "4.0":
                self.set_executables(
                    compiler='gcc -mno-cygwin -O2 -Wall',
                    compiler_so='gcc -mno-cygwin -O2 -Wall'
                                ' -Wstrict-prototypes',
                    linker_exe='g++ -mno-cygwin',
                    linker_so='g++ -mno-cygwin -shared')
            else:
                # gcc-4 series releases do not support -mno-cygwin option
                self.set_executables(compiler='gcc -O2 -Wall',
                                     compiler_so='gcc -O2 -Wall -Wstrict-prototypes',
                                     linker_exe='g++ ',
                                     linker_so='g++ -shared')
        # added for python2.3 support
        # we can't pass it through set_executables because pre 2.2 would fail
        self.compiler_cxx = ['g++']

        # Maybe we should also append -mthreads, but then the finished dlls
        # need another dll (mingwm10.dll see Mingw32 docs) (-mthreads: Support
        # thread-safe exception handling on `Mingw32')

        # no additional libraries needed
        #self.dll_libraries=[]
        return

    # __init__ ()

    def link(self,
             target_desc,
             objects,
             output_filename,
             output_dir,
             libraries,
             library_dirs,
             runtime_library_dirs,
             export_symbols = None,
             debug=0,
             extra_preargs=None,
             extra_postargs=None,
             build_temp=None,
             target_lang=None):
        # Include the appropiate MSVC runtime library if Python was built
        # with MSVC >= 7.0 (MinGW standard is msvcrt)
        runtime_library = msvc_runtime_library()
        if runtime_library:
            if not libraries:
                libraries = []
            libraries.append(runtime_library)
        args = (self,
                target_desc,
                objects,
                output_filename,
                output_dir,
                libraries,
                library_dirs,
                runtime_library_dirs,
                None, #export_symbols, we do this in our def-file
                debug,
                extra_preargs,
                extra_postargs,
                build_temp,
                target_lang)
        if self.gcc_version < "3.0.0":
            func = distutils.cygwinccompiler.CygwinCCompiler.link
        else:
            func = UnixCCompiler.link
        func(*args[:func.__code__.co_argcount])
        return

    def object_filenames (self,
                          source_filenames,
                          strip_dir=0,
                          output_dir=''):
        if output_dir is None: output_dir = ''
        obj_names = []
        for src_name in source_filenames:
            # use normcase to make sure '.rc' is really '.rc' and not '.RC'
            (base, ext) = os.path.splitext (os.path.normcase(src_name))

            # added these lines to strip off windows drive letters
            # without it, .o files are placed next to .c files
            # instead of the build directory
            drv, base = os.path.splitdrive(base)
            if drv:
                base = base[1:]

            if ext not in (self.src_extensions + ['.rc', '.res']):
                raise UnknownFileError(
                      "unknown file type '%s' (from '%s')" % \
                      (ext, src_name))
            if strip_dir:
                base = os.path.basename (base)
            if ext == '.res' or ext == '.rc':
                # these need to be compiled to object files
                obj_names.append (os.path.join (output_dir,
                                                base + ext + self.obj_extension))
            else:
                obj_names.append (os.path.join (output_dir,
                                                base + self.obj_extension))
        return obj_names

    # object_filenames ()


def find_python_dll():
    maj, min, micro = [int(i) for i in sys.version_info[:3]]
    dllname = 'python%d%d.dll' % (maj, min)
    print("Looking for %s" % dllname)

    # We can't do much here:
    # - find it in python main dir
    # - in system32,
    # - ortherwise (Sxs), I don't know how to get it.
    lib_dirs = [sys.prefix, os.path.join(sys.prefix, 'lib')]
    try:
        lib_dirs.append(os.path.join(os.environ['SYSTEMROOT'], 'system32'))
    except KeyError:
        pass

    for d in lib_dirs:
        dll = os.path.join(d, dllname)
        if os.path.exists(dll):
            return dll

    raise ValueError("%s not found in %s" % (dllname, lib_dirs))

def dump_table(dll):
    st = subprocess.Popen(["objdump.exe", "-p", dll], stdout=subprocess.PIPE)
    return st.stdout.readlines()

def generate_def(dll, dfile):
    """Given a dll file location,  get all its exported symbols and dump them
    into the given def file.

    The .def file will be overwritten"""
    dump = dump_table(dll)
    for i in range(len(dump)):
        if _START.match(dump[i].decode()):
            break
    else:
        raise ValueError("Symbol table not found")

    syms = []
    for j in range(i+1, len(dump)):
        m = _TABLE.match(dump[j].decode())
        if m:
            syms.append((int(m.group(1).strip()), m.group(2)))
        else:
            break

    if len(syms) == 0:
        log.warn('No symbols found in %s' % dll)

    d = open(dfile, 'w')
    d.write('LIBRARY        %s\n' % os.path.basename(dll))
    d.write(';CODE          PRELOAD MOVEABLE DISCARDABLE\n')
    d.write(';DATA          PRELOAD SINGLE\n')
    d.write('\nEXPORTS\n')
    for s in syms:
        #d.write('@%d    %s\n' % (s[0], s[1]))
        d.write('%s\n' % s[1])
    d.close()

def find_dll(dll_name):

    arch = {'AMD64' : 'amd64',
            'Intel' : 'x86'}[get_build_architecture()]

    def _find_dll_in_winsxs(dll_name):
        # Walk through the WinSxS directory to find the dll.
        winsxs_path = os.path.join(os.environ['WINDIR'], 'winsxs')
        if not os.path.exists(winsxs_path):
            return None
        for root, dirs, files in os.walk(winsxs_path):
            if dll_name in files and arch in root:
                return os.path.join(root, dll_name)
        return None

    def _find_dll_in_path(dll_name):
        # First, look in the Python directory, then scan PATH for
        # the given dll name.
        for path in [sys.prefix] + os.environ['PATH'].split(';'):
            filepath = os.path.join(path, dll_name)
            if os.path.exists(filepath):
                return os.path.abspath(filepath)

    return _find_dll_in_winsxs(dll_name) or _find_dll_in_path(dll_name)

def build_msvcr_library(debug=False):
    if os.name != 'nt':
        return False

    msvcr_name = msvc_runtime_library()

    # Skip using a custom library for versions < MSVC 8.0
    if int(msvcr_name.lstrip('msvcr')) < 80:
        log.debug('Skip building msvcr library:'
                  ' custom functionality not present')
        return False

    if debug:
        msvcr_name += 'd'

    # Skip if custom library already exists
    out_name = "lib%s.a" % msvcr_name
    out_file = os.path.join(sys.prefix, 'libs', out_name)
    if os.path.isfile(out_file):
        log.debug('Skip building msvcr library: "%s" exists' %
                  (out_file,))
        return True

    # Find the msvcr dll
    msvcr_dll_name = msvcr_name + '.dll'
    dll_file = find_dll(msvcr_dll_name)
    if not dll_file:
        log.warn('Cannot build msvcr library: "%s" not found' %
                 msvcr_dll_name)
        return False

    def_name = "lib%s.def" % msvcr_name
    def_file = os.path.join(sys.prefix, 'libs', def_name)

    log.info('Building msvcr library: "%s" (from %s)' \
             % (out_file, dll_file))

    # Generate a symbol definition file from the msvcr dll
    generate_def(dll_file, def_file)

    # Create a custom mingw library for the given symbol definitions
    cmd = ['dlltool', '-d', def_file, '-l', out_file]
    retcode = subprocess.call(cmd)

    # Clean up symbol definitions
    os.remove(def_file)

    return (not retcode)

def build_import_library():
    if os.name != 'nt':
        return

    arch = get_build_architecture()
    if arch == 'AMD64':
        return _build_import_library_amd64()
    elif arch == 'Intel':
        return _build_import_library_x86()
    else:
        raise ValueError("Unhandled arch %s" % arch)

def _build_import_library_amd64():
    dll_file = find_python_dll()

    out_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
    out_file = os.path.join(sys.prefix, 'libs', out_name)
    if os.path.isfile(out_file):
        log.debug('Skip building import library: "%s" exists' %
                  (out_file))
        return

    def_name = "python%d%d.def" % tuple(sys.version_info[:2])
    def_file = os.path.join(sys.prefix, 'libs', def_name)

    log.info('Building import library (arch=AMD64): "%s" (from %s)' %
             (out_file, dll_file))

    generate_def(dll_file, def_file)

    cmd = ['dlltool', '-d', def_file, '-l', out_file]
    subprocess.Popen(cmd)

def _build_import_library_x86():
    """ Build the import libraries for Mingw32-gcc on Windows
    """
    lib_name = "python%d%d.lib" % tuple(sys.version_info[:2])
    lib_file = os.path.join(sys.prefix, 'libs', lib_name)
    out_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
    out_file = os.path.join(sys.prefix, 'libs', out_name)
    if not os.path.isfile(lib_file):
        log.warn('Cannot build import library: "%s" not found' % (lib_file))
        return
    if os.path.isfile(out_file):
        log.debug('Skip building import library: "%s" exists' % (out_file))
        return
    log.info('Building import library (ARCH=x86): "%s"' % (out_file))

    from numpy.distutils import lib2def

    def_name = "python%d%d.def" % tuple(sys.version_info[:2])
    def_file = os.path.join(sys.prefix, 'libs', def_name)
    nm_cmd = '%s %s' % (lib2def.DEFAULT_NM, lib_file)
    nm_output = lib2def.getnm(nm_cmd)
    dlist, flist = lib2def.parse_nm(nm_output)
    lib2def.output_def(dlist, flist, lib2def.DEF_HEADER, open(def_file, 'w'))

    dll_name = "python%d%d.dll" % tuple(sys.version_info[:2])
    args = (dll_name, def_file, out_file)
    cmd = 'dlltool --dllname %s --def %s --output-lib %s' % args
    status = os.system(cmd)
    # for now, fail silently
    if status:
        log.warn('Failed to build import library for gcc. Linking will fail.')
    return

#=====================================
# Dealing with Visual Studio MANIFESTS
#=====================================

# Functions to deal with visual studio manifests. Manifest are a mechanism to
# enforce strong DLL versioning on windows, and has nothing to do with
# distutils MANIFEST. manifests are XML files with version info, and used by
# the OS loader; they are necessary when linking against a DLL not in the
# system path; in particular, official python 2.6 binary is built against the
# MS runtime 9 (the one from VS 2008), which is not available on most windows
# systems; python 2.6 installer does install it in the Win SxS (Side by side)
# directory, but this requires the manifest for this to work. This is a big
# mess, thanks MS for a wonderful system.

# XXX: ideally, we should use exactly the same version as used by python. I
# submitted a patch to get this version, but it was only included for python
# 2.6.1 and above. So for versions below, we use a "best guess".
_MSVCRVER_TO_FULLVER = {}
if sys.platform == 'win32':
    try:
        import msvcrt
        # I took one version in my SxS directory: no idea if it is the good
        # one, and we can't retrieve it from python
        _MSVCRVER_TO_FULLVER['80'] = "8.0.50727.42"
        _MSVCRVER_TO_FULLVER['90'] = "9.0.21022.8"
        # Value from msvcrt.CRT_ASSEMBLY_VERSION under Python 3.3.0
        # on Windows XP:
        _MSVCRVER_TO_FULLVER['100'] = "10.0.30319.460"
        if hasattr(msvcrt, "CRT_ASSEMBLY_VERSION"):
            major, minor, rest = msvcrt.CRT_ASSEMBLY_VERSION.split(".", 2)
            _MSVCRVER_TO_FULLVER[major + minor] = msvcrt.CRT_ASSEMBLY_VERSION
            del major, minor, rest
    except ImportError:
        # If we are here, means python was not built with MSVC. Not sure what
        # to do in that case: manifest building will fail, but it should not be
        # used in that case anyway
        log.warn('Cannot import msvcrt: using manifest will not be possible')

def msvc_manifest_xml(maj, min):
    """Given a major and minor version of the MSVCR, returns the
    corresponding XML file."""
    try:
        fullver = _MSVCRVER_TO_FULLVER[str(maj * 10 + min)]
    except KeyError:
        raise ValueError("Version %d,%d of MSVCRT not supported yet" %
                         (maj, min))
    # Don't be fooled, it looks like an XML, but it is not. In particular, it
    # should not have any space before starting, and its size should be
    # divisible by 4, most likely for alignement constraints when the xml is
    # embedded in the binary...
    # This template was copied directly from the python 2.6 binary (using
    # strings.exe from mingw on python.exe).
    template = """\
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"></requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.VC%(maj)d%(min)d.CRT" version="%(fullver)s" processorArchitecture="*" publicKeyToken="1fc8b3b9a1e18e3b"></assemblyIdentity>
    </dependentAssembly>
  </dependency>
</assembly>"""

    return template % {'fullver': fullver, 'maj': maj, 'min': min}

def manifest_rc(name, type='dll'):
    """Return the rc file used to generate the res file which will be embedded
    as manifest for given manifest file name, of given type ('dll' or
    'exe').

    Parameters
    ----------
    name : str
            name of the manifest file to embed
    type : str {'dll', 'exe'}
            type of the binary which will embed the manifest

    """
    if type == 'dll':
        rctype = 2
    elif type == 'exe':
        rctype = 1
    else:
        raise ValueError("Type %s not supported" % type)

    return """\
#include "winuser.h"
%d RT_MANIFEST %s""" % (rctype, name)

def check_embedded_msvcr_match_linked(msver):
    """msver is the ms runtime version used for the MANIFEST."""
    # check msvcr major version are the same for linking and
    # embedding
    msvcv = msvc_runtime_library()
    if msvcv:
        assert msvcv.startswith("msvcr"), msvcv
        # Dealing with something like "mscvr90" or "mscvr100", the last
        # last digit is the minor release, want int("9") or int("10"):
        maj = int(msvcv[5:-1])
        if not maj == int(msver):
            raise ValueError(
                  "Discrepancy between linked msvcr " \
                  "(%d) and the one about to be embedded " \
                  "(%d)" % (int(msver), maj))

def configtest_name(config):
    base = os.path.basename(config._gen_temp_sourcefile("yo", [], "c"))
    return os.path.splitext(base)[0]

def manifest_name(config):
    # Get configest name (including suffix)
    root = configtest_name(config)
    exext = config.compiler.exe_extension
    return root + exext + ".manifest"

def rc_name(config):
    # Get configtest name (including suffix)
    root = configtest_name(config)
    return root + ".rc"

def generate_manifest(config):
    msver = get_build_msvc_version()
    if msver is not None:
        if msver >= 8:
            check_embedded_msvcr_match_linked(msver)
            ma = int(msver)
            mi = int((msver - ma) * 10)
            # Write the manifest file
            manxml = msvc_manifest_xml(ma, mi)
            man = open(manifest_name(config), "w")
            config.temp_files.append(manifest_name(config))
            man.write(manxml)
            man.close()
