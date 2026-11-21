#!/usr/bin/env bash
# Install homenet into ~/.local/bin.
#   curl -fsSL https://raw.githubusercontent.com/graydeon/homenet/main/install.sh | bash
set -euo pipefail

VERSION=${VERSION:-v0.1.0}
BASE=${BASE:-https://raw.githubusercontent.com/graydeon/homenet/$VERSION}

die() { echo "install.sh: $*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 not found; install it first (Debian/Ubuntu: sudo apt install python3)"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' ||
    die "python3 >= 3.11 required; found $(python3 -V 2>&1) (Debian/Ubuntu: sudo apt install python3)"
command -v dig >/dev/null || die "dig not found (Debian/Ubuntu: sudo apt install dnsutils)"
command -v curl >/dev/null || die "curl not found (Debian/Ubuntu: sudo apt install curl)"

mkdir -p "$HOME/.local/bin"
self=${BASH_SOURCE[0]:-}
if [[ $self == */* ]] && [ -f "$(dirname "$self")/homenet" ]; then
    install -m 755 "$(dirname "$self")/homenet" "$HOME/.local/bin/homenet"
else
    curl -fsSL "$BASE/homenet" -o "$HOME/.local/bin/homenet"
    chmod 755 "$HOME/.local/bin/homenet"
fi

case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) echo "note: ~/.local/bin is not on PATH; add this line to ~/.profile:"
       echo '  export PATH="$HOME/.local/bin:$PATH"' ;;
esac

echo "homenet installed to $HOME/.local/bin/homenet"
echo "next: homenet init"
