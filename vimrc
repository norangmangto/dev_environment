set nocompatible

syntax on
"colorscheme evening
set background=dark

set encoding=utf-8
filetype indent plugin on

set number
"set numberwidth=6
set ruler

set autoindent
set smartindent
set tabstop=4
set shiftwidth=4
set expandtab

set nowrap
set hlsearch
set incsearch

set showtabline=2

"set scrolloff=5

set wildmode=longest:full
set wildmenu

" auto-completion
set omnifunc=syntaxcomplete#Complete

map <C-P> :tabp<CR>
map <C-N> :tabn<CR>
"map <C-I> :tabe<CR>

"let &colorcolumn=join(range(81,81),",")
""let &colorcolumn="80,".join(range(100,100),",")
"highlight ColorColumn ctermbg=darkblue guibg=darkblue
""highlight OverLength ctermbg=darkred ctermfg=white guibg=darkred
"match OverLength /\%100v.*/
