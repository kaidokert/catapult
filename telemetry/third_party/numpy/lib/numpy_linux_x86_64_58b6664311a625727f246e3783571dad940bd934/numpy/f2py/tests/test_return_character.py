from __future__ import division, absolute_import, print_function

from numpy import array
from numpy.compat import asbytes
from numpy.testing import run_module_suite, assert_, dec
import util


class TestReturnCharacter(util.F2PyTest):

    def check_function(self, t):
        tname = t.__doc__.split()[0]
        if tname in ['t0', 't1', 's0', 's1']:
            assert_(t(23) == asbytes('2'))
            r = t('ab')
            assert_(r == asbytes('a'), repr(r))
            r = t(array('ab'))
            assert_(r == asbytes('a'), repr(r))
            r = t(array(77, 'u1'))
            assert_(r == asbytes('M'), repr(r))
            #assert_(_raises(ValueError, t, array([77,87])))
            #assert_(_raises(ValueError, t, array(77)))
        elif tname in ['ts', 'ss']:
            assert_(t(23) == asbytes('23        '), repr(t(23)))
            assert_(t('123456789abcdef') == asbytes('123456789a'))
        elif tname in ['t5', 's5']:
            assert_(t(23) == asbytes('23   '), repr(t(23)))
            assert_(t('ab') == asbytes('ab   '), repr(t('ab')))
            assert_(t('123456789abcdef') == asbytes('12345'))
        else:
            raise NotImplementedError


class TestF77ReturnCharacter(TestReturnCharacter):
    code = """
       function t0(value)
         character value
         character t0
         t0 = value
       end
       function t1(value)
         character*1 value
         character*1 t1
         t1 = value
       end
       function t5(value)
         character*5 value
         character*5 t5
         t5 = value
       end
       function ts(value)
         character*(*) value
         character*(*) ts
         ts = value
       end

       subroutine s0(t0,value)
         character value
         character t0
cf2py    intent(out) t0
         t0 = value
       end
       subroutine s1(t1,value)
         character*1 value
         character*1 t1
cf2py    intent(out) t1
         t1 = value
       end
       subroutine s5(t5,value)
         character*5 value
         character*5 t5
cf2py    intent(out) t5
         t5 = value
       end
       subroutine ss(ts,value)
         character*(*) value
         character*10 ts
cf2py    intent(out) ts
         ts = value
       end
    """

    @dec.slow
    def test_all(self):
        for name in "t0,t1,t5,s0,s1,s5,ss".split(","):
            self.check_function(getattr(self.module, name))


class TestF90ReturnCharacter(TestReturnCharacter):
    suffix = ".f90"
    code = """
module f90_return_char
  contains
       function t0(value)
         character :: value
         character :: t0
         t0 = value
       end function t0
       function t1(value)
         character(len=1) :: value
         character(len=1) :: t1
         t1 = value
       end function t1
       function t5(value)
         character(len=5) :: value
         character(len=5) :: t5
         t5 = value
       end function t5
       function ts(value)
         character(len=*) :: value
         character(len=10) :: ts
         ts = value
       end function ts

       subroutine s0(t0,value)
         character :: value
         character :: t0
!f2py    intent(out) t0
         t0 = value
       end subroutine s0
       subroutine s1(t1,value)
         character(len=1) :: value
         character(len=1) :: t1
!f2py    intent(out) t1
         t1 = value
       end subroutine s1
       subroutine s5(t5,value)
         character(len=5) :: value
         character(len=5) :: t5
!f2py    intent(out) t5
         t5 = value
       end subroutine s5
       subroutine ss(ts,value)
         character(len=*) :: value
         character(len=10) :: ts
!f2py    intent(out) ts
         ts = value
       end subroutine ss
end module f90_return_char
    """

    @dec.slow
    def test_all(self):
        for name in "t0,t1,t5,ts,s0,s1,s5,ss".split(","):
            self.check_function(getattr(self.module.f90_return_char, name))

if __name__ == "__main__":
    run_module_suite()
