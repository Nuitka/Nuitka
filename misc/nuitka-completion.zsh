# Nuitka zsh completion
# spell-checker: disable
# To use this in your shell, source this file.
#
# This file is in the public domain.

_nuitka_completion() {
  local -a matches

  # For compctl (older zsh) fallback
  if ! type compadd >/dev/null 2>&1; then
    local line point cwords cword
    read -l line
    read -ln point
    read -Ac cwords
    read -cn cword
    reply=( $( COMP_LINE="$line" COMP_POINT=$(( point-1 )) \
               COMP_WORDS="$cwords[*]" COMP_CWORD=$(( cword-1 )) \
               OPTPARSE_AUTO_COMPLETE=1 SHELL=zsh $cwords[1] ) )
    return
  fi

  # Modern zsh compsys
  matches=( $( COMP_LINE="$BUFFER" COMP_POINT=$CURSOR \
               COMP_WORDS="${words[*]}" COMP_CWORD=$(( CURRENT-1 )) \
               OPTPARSE_AUTO_COMPLETE=1 SHELL=zsh $words[1] ) )

  if [[ ${words[CURRENT]} == *=* ]]; then
      compset -P '*='
  fi

  if [[ ${#matches[@]} -eq 1 && ${matches[1]} == *= ]]; then
      compadd -S '' -a matches
  else
      compadd -a matches
  fi
}

# Try modern compsys first
if type compdef >/dev/null 2>&1; then
    compdef _nuitka_completion nuitka nuitka-run nuitka3 nuitka3-run
else
    # Fallback to compctl
    compctl -K _nuitka_completion nuitka
    compctl -K _nuitka_completion nuitka-run
    compctl -K _nuitka_completion nuitka3
    compctl -K _nuitka_completion nuitka3-run
fi
