grammar           = tagged_list end
                    -> _1
                  | simple_list end
                    -> _1

simple_list       = (sp* simple_line:l1 '\n' -> l1 )* sp* simple_line?
                    -> _1 + _3

simple_line       = '-' {test_glob} trailing_comment
                    -> [ 'rule', '', [], _2, [ 'Skip' ], _3 ]
                  | {test_glob} trailing_comment
                    -> [ 'rule', '', [], _1, [ 'Pass' ], _2 ]
                  | {comment}
                    -> [ 'comment',  _1 ]
                  | sp*
                    -> [ 'blank' ]

trailing_comment  = sp* ((comment:c -> c) | -> '')

tagged_list       = starting_comments tagged_lines
                    -> _1 + _2

tagged_lines      = (sp* tagged_line:l '\n' -> l )* sp* tagged_line?
                    -> _1 + _3

starting_comments = (starting_comment:c '\n' -> c )*
                    -> _1

starting_comment  = duplicates_decl
                    -> _1
                  | tags_decl
                    -> _1
                  | {comment}
                    -> [ 'comment', _1 ]

duplicates_decl   = '# duplicates:' sp+ {('allowed' | 'error')}
                    -> [ 't_duplicates', _3 ]

tags_decl         = '# tags:' sp+ '[' (sp+ tag:t1 -> t1)+
                    ('\n#' (sp+ tag:t3 -> t3)*:t4 -> t4)* sp+ ']'
                    -> [ 't_tag', _4 + _5 ]

tagged_line       = (({bug_id}:b sp+ -> b) | '') opt_tags
                    {test_glob} sp+ results trailing_comment
                    -> ['rule', _1, _2, _3, _5, _6]
                  | {comment}
                    -> ['comment', _1]
                  | sp*
                    -> ['blank']

opt_tags          = tags sp+
                    -> _1
                  | -> []

test_glob         = id

id                = (~(' ' | '#' | '\n' | '[' | ']') anything)+

tags              = '[' (sp+ {tag}:t -> t)+ sp+ ']'
                    -> _2

results           = '[' (sp+ {result}:r -> r)+ sp+ ']'
                    -> _2

tag               = ~result ~bug_id id

bug_id            = 'crbug.com/' ('0'..'9')+  | 'Bug(' id ')'

result            = 'Crash' | 'Fail' | 'Pass' | 'Skip'
                  | 'Slow' | 'Timeout' | 'WontFix'

comment           = '#' (~'\n' ~end anything)*

sp                = ' '
