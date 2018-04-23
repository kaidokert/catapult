import re
import sys

if sys.version_info[0] < 3:
    # pylint: disable=redefined-builtin
    chr = unichr
    str = unicode

# pylint: disable=line-too-long


class Parser(object):
    def __init__(self, msg, fname):
        self.msg = str(msg)
        self.end = len(self.msg)
        self.fname = fname
        self.val = None
        self.pos = 0
        self.failed = False
        self.errpos = 0
        self._regexps = {}
        self._scopes = []

    def parse(self):
        self._r_grammar()
        if self.failed:
            return self._h_err()
        return self.val, None, self.pos

    def _r_grammar(self):
        self._h_choose([self._s_grammar_c0,
                        self._s_grammar_c1])

    def _s_grammar_c0(self):
        self._h_scope('grammar', [lambda: self._h_bind(self._r_tagged_list, '_1'),
                                  self._r_end,
                                  lambda: self._h_succeed(self._h_get('_1'))])

    def _s_grammar_c1(self):
        self._h_scope('grammar', [lambda: self._h_bind(self._r_simple_list, '_1'),
                                  self._r_end,
                                  lambda: self._h_succeed(self._h_get('_1'))])

    def _r_simple_list(self):
        self._h_scope('simple_list', [lambda: self._h_bind(lambda: self._h_star(self._s_simple_list_s0_l_s), '_1'),
                                      lambda: self._h_re('( )*'),
                                      lambda: self._h_bind(lambda: self._h_opt(self._r_simple_line), '_3'),
                                      lambda: self._h_succeed(self._h_get('_1') + self._h_get('_3'))])

    def _s_simple_list_s0_l_s(self):
        self._h_seq([lambda: self._h_star(self._r_sp),
                     lambda: self._h_bind(self._r_simple_line, 'l1'),
                     lambda: self._h_ch('\n'),
                     lambda: self._h_succeed(self._h_get('l1'))])

    def _r_simple_line(self):
        self._h_choose([self._s_simple_line_c0,
                        self._s_simple_line_c1,
                        self._s_simple_line_c2,
                        self._s_simple_line_c3])

    def _s_simple_line_c0(self):
        self._h_scope('simple_line', [lambda: self._h_ch('-'),
                                      lambda: self._h_bind(lambda: self._h_capture(self._r_test_glob), '_2'),
                                      lambda: self._h_bind(self._r_trailing_comment, '_3'),
                                      lambda: self._h_succeed(['rule', '', [], self._h_get('_2'), ['Skip'], self._h_get('_3')])])

    def _s_simple_line_c1(self):
        self._h_scope('simple_line', [lambda: self._h_bind(lambda: self._h_capture(self._r_test_glob), '_1'),
                                      lambda: self._h_bind(self._r_trailing_comment, '_2'),
                                      lambda: self._h_succeed(['rule', '', [], self._h_get('_1'), ['Pass'], self._h_get('_2')])])

    def _s_simple_line_c2(self):
        self._h_scope('simple_line', [lambda: self._h_bind(lambda: self._h_capture(self._r_comment), '_1'),
                                      lambda: self._h_succeed(['comment', self._h_get('_1')])])

    def _s_simple_line_c3(self):
        self._h_seq([lambda: self._h_star(self._r_sp),
                     lambda: self._h_succeed(['blank'])])

    def _r_trailing_comment(self):
        self._h_scope('trailing_comment', [lambda: self._h_re('( )*'),
                                           self._s_trailing_comment_s1])

    def _s_trailing_comment_s1(self):
        self._h_choose([self._s_trailing_comment_s1_c0,
                        lambda: self._h_succeed('')])

    def _s_trailing_comment_s1_c0(self):
        self._h_seq([lambda: self._h_bind(self._r_comment, 'c'),
                     lambda: self._h_succeed(self._h_get('c'))])

    def _r_tagged_list(self):
        self._h_scope('tagged_list', [lambda: self._h_bind(self._r_starting_comments, '_1'),
                                      lambda: self._h_bind(self._r_tagged_lines, '_2'),
                                      lambda: self._h_succeed(self._h_get('_1') + self._h_get('_2'))])

    def _r_tagged_lines(self):
        self._h_scope('tagged_lines', [lambda: self._h_bind(lambda: self._h_star(self._s_tagged_lines_s0_l_s), '_1'),
                                       lambda: self._h_re('( )*'),
                                       lambda: self._h_bind(lambda: self._h_opt(self._r_tagged_line), '_3'),
                                       lambda: self._h_succeed(self._h_get('_1') + self._h_get('_3'))])

    def _s_tagged_lines_s0_l_s(self):
        self._h_seq([lambda: self._h_star(self._r_sp),
                     lambda: self._h_bind(self._r_tagged_line, 'l'),
                     lambda: self._h_ch('\n'),
                     lambda: self._h_succeed(self._h_get('l'))])

    def _r_starting_comments(self):
        self._h_scope('starting_comments', [lambda: self._h_bind(lambda: self._h_star(self._s_starting_comments_s0_l_s), '_1'),
                                            lambda: self._h_succeed(self._h_get('_1'))])

    def _s_starting_comments_s0_l_s(self):
        self._h_seq([lambda: self._h_bind(self._r_starting_comment, 'c'),
                     lambda: self._h_ch('\n'),
                     lambda: self._h_succeed(self._h_get('c'))])

    def _r_starting_comment(self):
        self._h_choose([self._s_starting_comment_c0,
                        self._s_starting_comment_c1,
                        self._s_starting_comment_c2])

    def _s_starting_comment_c0(self):
        self._h_scope('starting_comment', [lambda: self._h_bind(self._r_duplicates_decl, '_1'),
                                           lambda: self._h_succeed(self._h_get('_1'))])

    def _s_starting_comment_c1(self):
        self._h_scope('starting_comment', [lambda: self._h_bind(self._r_tags_decl, '_1'),
                                           lambda: self._h_succeed(self._h_get('_1'))])

    def _s_starting_comment_c2(self):
        self._h_scope('starting_comment', [lambda: self._h_bind(lambda: self._h_capture(self._r_comment), '_1'),
                                           lambda: self._h_succeed(['comment', self._h_get('_1')])])

    def _r_duplicates_decl(self):
        self._h_scope('duplicates_decl', [lambda: self._h_re('# duplicates:( )+'),
                                          lambda: self._h_bind(lambda: self._h_capture(self._s_duplicates_decl_s1_l_c), '_3'),
                                          lambda: self._h_succeed(['t_duplicates', self._h_get('_3')])])

    def _s_duplicates_decl_s1_l_c(self):
        self._h_choose([lambda: self._h_str('allowed', 7),
                        lambda: self._h_str('error', 5)])

    def _r_tags_decl(self):
        self._h_scope('tags_decl', [lambda: self._h_re('# tags:( )+\\['),
                                    lambda: self._h_bind(lambda: self._h_plus(self._s_tags_decl_s1_l_p), '_4'),
                                    lambda: self._h_bind(lambda: self._h_star(self._s_tags_decl_s2_l_s), '_5'),
                                    lambda: self._h_re('( )+\\]'),
                                    lambda: self._h_succeed(['t_tag', self._h_get('_4') + self._h_get('_5')])])

    def _s_tags_decl_s1_l_p(self):
        self._h_seq([lambda: self._h_plus(self._r_sp),
                     lambda: self._h_bind(self._r_tag, 't1'),
                     lambda: self._h_succeed(self._h_get('t1'))])

    def _s_tags_decl_s2_l_s(self):
        self._h_seq([lambda: self._h_str('\n#', 2),
                     lambda: self._h_bind(lambda: self._h_star(self._s_tags_decl_s2_l_s_s1_l_s), 't4'),
                     lambda: self._h_succeed(self._h_get('t4'))])

    def _s_tags_decl_s2_l_s_s1_l_s(self):
        self._h_seq([lambda: self._h_plus(self._r_sp),
                     lambda: self._h_bind(self._r_tag, 't3'),
                     lambda: self._h_succeed(self._h_get('t3'))])

    def _r_tagged_line(self):
        self._h_choose([self._s_tagged_line_c0,
                        self._s_tagged_line_c1,
                        self._s_tagged_line_c2])

    def _s_tagged_line_c0(self):
        self._h_scope('tagged_line', [lambda: self._h_bind(self._s_tagged_line_c0_s0_l, '_1'),
                                      lambda: self._h_bind(self._r_opt_tags, '_2'),
                                      lambda: self._h_bind(lambda: self._h_capture(self._r_test_glob), '_3'),
                                      lambda: self._h_plus(self._r_sp),
                                      lambda: self._h_bind(self._r_results, '_5'),
                                      lambda: self._h_bind(self._r_trailing_comment, '_6'),
                                      lambda: self._h_succeed(['rule', self._h_get('_1'), self._h_get('_2'), self._h_get('_3'), self._h_get('_5'), self._h_get('_6')])])

    def _s_tagged_line_c0_s0_l(self):
        self._h_choose([self._s_tagged_line_c0_s0_l_c0,
                        lambda: self._h_str('', 0)])

    def _s_tagged_line_c0_s0_l_c0(self):
        self._h_seq([lambda: self._h_bind(lambda: self._h_capture(self._r_bug_id), 'b'),
                     lambda: self._h_plus(self._r_sp),
                     lambda: self._h_succeed(self._h_get('b'))])

    def _s_tagged_line_c1(self):
        self._h_scope('tagged_line', [lambda: self._h_bind(lambda: self._h_capture(self._r_comment), '_1'),
                                      lambda: self._h_succeed(['comment', self._h_get('_1')])])

    def _s_tagged_line_c2(self):
        self._h_seq([lambda: self._h_star(self._r_sp),
                     lambda: self._h_succeed(['blank'])])

    def _r_opt_tags(self):
        self._h_choose([self._s_opt_tags_c0,
                        lambda: self._h_succeed([])])

    def _s_opt_tags_c0(self):
        self._h_scope('opt_tags', [lambda: self._h_bind(self._r_tags, '_1'),
                                   lambda: self._h_plus(self._r_sp),
                                   lambda: self._h_succeed(self._h_get('_1'))])

    def _r_test_glob(self):
        self._r_id()

    def _r_id(self):
        self._h_re('((?!( |#|\n|\\[|\\])).)+')

    def _r_tags(self):
        self._h_scope('tags', [lambda: self._h_re('\\['),
                               lambda: self._h_bind(lambda: self._h_plus(self._s_tags_s1_l_p), '_2'),
                               lambda: self._h_re('( )+\\]'),
                               lambda: self._h_succeed(self._h_get('_2'))])

    def _s_tags_s1_l_p(self):
        self._h_seq([lambda: self._h_plus(self._r_sp),
                     lambda: self._h_bind(lambda: self._h_capture(self._r_tag), 't'),
                     lambda: self._h_succeed(self._h_get('t'))])

    def _r_results(self):
        self._h_scope('results', [lambda: self._h_re('\\['),
                                  lambda: self._h_bind(lambda: self._h_plus(self._s_results_s1_l_p), '_2'),
                                  lambda: self._h_re('( )+\\]'),
                                  lambda: self._h_succeed(self._h_get('_2'))])

    def _s_results_s1_l_p(self):
        self._h_seq([lambda: self._h_plus(self._r_sp),
                     lambda: self._h_bind(lambda: self._h_capture(self._r_result), 'r'),
                     lambda: self._h_succeed(self._h_get('r'))])

    def _r_tag(self):
        self._h_re('(?!(Crash|Fail|Pass|Skip|Slow|Timeout|WontFix))(?!(crbug\\.com/([0-9])+|Bug\\(((?!( |#|\n|\\[|\\])).)+\\)))((?!( |#|\n|\\[|\\])).)+')

    def _r_bug_id(self):
        self._h_re('(crbug\\.com/([0-9])+|Bug\\(((?!( |#|\n|\\[|\\])).)+\\))')

    def _r_result(self):
        self._h_re('(Crash|Fail|Pass|Skip|Slow|Timeout|WontFix)')

    def _r_comment(self):
        self._h_seq([lambda: self._h_re('#'),
                     lambda: self._h_star(self._s_comment_s1_s)])

    def _s_comment_s1_s(self):
        self._h_seq([lambda: self._h_re('(?!\n)'),
                     lambda: self._h_not(self._r_end),
                     lambda: self._h_re('.')])

    def _r_sp(self):
        self._h_ch(' ')

    def _r_end(self):
        if self.pos == self.end:
            self._h_succeed(None)
        else:
            self._h_fail()

    def _h_bind(self, rule, var):
        rule()
        if not self.failed:
            self._h_set(var, self.val)

    def _h_capture(self, rule):
        start = self.pos
        rule()
        if not self.failed:
            self._h_succeed(self.msg[start:self.pos],
                            self.pos)

    def _h_ch(self, ch):
        p = self.pos
        if p < self.end and self.msg[p] == ch:
            self._h_succeed(ch, p + 1)
        else:
            self._h_fail()

    def _h_choose(self, rules):
        p = self.pos
        for rule in rules[:-1]:
            rule()
            if not self.failed:
                return
            self._h_rewind(p)
        rules[-1]()

    def _h_err(self):
        lineno = 1
        colno = 1
        for ch in self.msg[:self.errpos]:
            if ch == '\n':
                lineno += 1
                colno = 1
            else:
                colno += 1
        if self.errpos == len(self.msg):
            thing = 'end of input'
        else:
            thing = repr(self.msg[self.errpos])
            if thing[0] == 'u':
                thing = thing[1:]
        err_str = '%s:%d Unexpected %s at column %d' % (self.fname, lineno,
                                                        thing, colno)
        return None, err_str, self.errpos

    def _h_fail(self):
        self.val = None
        self.failed = True
        if self.pos >= self.errpos:
            self.errpos = self.pos

    def _h_get(self, var):
        return self._scopes[-1][1][var]

    def _h_not(self, rule):
        p = self.pos
        rule()
        if self.failed:
            self._h_succeed(None, p)
        else:
            self._h_rewind(p)
            self._h_fail()

    def _h_opt(self, rule):
        p = self.pos
        rule()
        if self.failed:
            self._h_succeed([], p)
        else:
            self._h_succeed([self.val])

    def _h_plus(self, rule):
        vs = []
        rule()
        if self.failed:
            return
        vs = [self.val]
        while not self.failed:
            p = self.pos
            rule()
            if self.failed:
                self._h_rewind(p)
                break
            else:
                vs.append(self.val)
        self._h_succeed(vs)

    def _h_re(self, pattern):
        try:
            pat = self._regexps[pattern]
        except KeyError as e:
            pat = self._regexps.setdefault(pattern, re.compile(pattern, flags=re.DOTALL))
        m = pat.match(self.msg, self.pos, self.end)
        if m:
            self._h_succeed(m.group(0), self.pos + len(m.group(0)))
        else:
            self._h_fail()

    def _h_rewind(self, pos):
        self._h_succeed(None, pos)

    def _h_scope(self, name, rules):
        self._scopes.append((name, {}))
        for rule in rules:
            rule()
            if self.failed:
                self._scopes.pop()
                return
        self._scopes.pop()

    def _h_seq(self, rules):
        for rule in rules:
            rule()
            if self.failed:
                return

    def _h_set(self, var, val):
        self._scopes[-1][1][var] = val

    def _h_star(self, rule):
        vs = []
        while not self.failed:
            p = self.pos
            rule()
            if self.failed:
                self._h_rewind(p)
                break
            else:
                vs.append(self.val)
        self._h_succeed(vs)

    def _h_str(self, s, l):
        p = self.pos
        if (p + l <= self.end) and self.msg[p:p + l] == s:
            self._h_succeed(s, self.pos + l)
        else:
            self._h_fail()

    def _h_succeed(self, v, newpos=None):
        self.val = v
        self.failed = False
        if newpos is not None:
            self.pos = newpos
