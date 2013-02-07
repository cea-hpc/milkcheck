
" Vim syntax file for MilkCheck config files

" For version 5.x: Clear all syntax items
" For version 6.x: Quit when a syntax file was already loaded
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

" Read the yaml syntax to start with
if version < 600
  so <sfile>:p:h/yaml.vim
else
  runtime! syntax/yaml.vim
  unlet b:current_syntax
endif

" Redefine yamlKey
syn match   yamlKey     '\(\w\|,\|-\)\+\(\s\+\(\w\|,\|-\)\+\)*\ze\s*:' contains=mlkKeyword,mlkKeyDelim

syn match   mlkKeyDelim  contained ','
syn keyword mlkKeyword   contained variables services actions
syn keyword mlkKeyword   contained require before
syn keyword mlkKeyword   contained desc target mode cmd fanout timeout errors
syn keyword mlkKeyword   contained delay retry
syn match   mlkVariable  '%\h\w*'
syn match   mlkNodeGroup '@\w\+'

" Define the default highlighting.
" For version 5.7 and earlier: only when not done already
" For version 5.8 and later: only when an item doesn't have highlighting yet
if version >= 508 || !exists("did_clushconf_syntax_inits")
  if version < 508
    let did_clushconf_syntax_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  HiLink mlkKeyword   Keyword
  HiLink mlkKeyDelim  Delimiter
  HiLink mlkVariable  Identifier
  HiLink mlkNodeGroup Error

  delcommand HiLink
endif

let b:current_syntax = "milkcheck"

" vim:ts=8
