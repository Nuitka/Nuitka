# Nuitka bash completion
# spell-checker: disable
# To use this in your shell, source this file or place it in
# /etc/bash_completion.d/ to have it automatically load.
#
# This file is in the public domain.

_nuitka_completion()
{
    # needed to let it return _filedir based commands
    local cur prev quoted

    # Use bash-completion functions if available
    if type _get_comp_words_by_ref >/dev/null 2>&1; then
        _get_comp_words_by_ref cur prev
        _quote_readline_by_ref "$cur" quoted
        _expand || return 0
    fi

    # call the command with the completion information, then eval its results so it can call _filedir or similar
    eval $( \
            COMP_LINE=$COMP_LINE  COMP_POINT=$COMP_POINT \
            COMP_WORDS="${COMP_WORDS[*]}"  COMP_CWORD=$COMP_CWORD \
            OPTPARSE_AUTO_COMPLETE=1 SHELL=bash $1
        )

    # If there is exactly one completion and it ends with '=', disable the trailing space
    if [[ ${#COMPREPLY[@]} -eq 1 && ${COMPREPLY[0]} == *= ]]; then
        compopt -o nospace 2>/dev/null
    fi
}

complete -F _nuitka_completion nuitka
complete -F _nuitka_completion nuitka-run
complete -F _nuitka_completion nuitka3
complete -F _nuitka_completion nuitka3-run
