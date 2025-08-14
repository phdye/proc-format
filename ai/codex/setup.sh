#!/usr/bin/env bash
set -euo pipefail

ASSET="python-3.2.5.ubuntu-20.04.v1.1.5.tar.xz"
REPO="phdye/python-3.2.5-repack"
INSTALL_DIR="/opt/python-3.2.5"
TARBALL="$ASSET"

# Prerequisite: jq must be installed
command -v jq >/dev/null || { echo "❌ jq is required. Please install it."; exit 1; }

echo "🔍 Locating release asset for $ASSET..."

# Use full /releases API to find asset
DOWNLOAD_URL=$(curl -s "https://api.github.com/repos/$REPO/releases" |
  jq -r --arg name "$ASSET" '.[] | .assets[]? | select(.name == $name) | .browser_download_url' | head -n1)

if [[ -z "$DOWNLOAD_URL" ]]; then
  echo "❌ Asset $ASSET not found in any public releases of $REPO"
  exit 1
fi

echo "✅ Found asset:"
echo "  $DOWNLOAD_URL"

echo "⬇️ Downloading..."
curl -L -o "$TARBALL" "$DOWNLOAD_URL"

echo "📦 Extracting to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
tar -xf "$TARBALL" -C "$INSTALL_DIR" --strip-components=1
export LD_LIBRARY_PATH=/opt/python-3.2.5/lib
echo /opt/python-3.2.5/lib > /etc/ld.so.conf.d/zz~python-3.2.5.conf
echo 'export PATH="/opt/python-3.2.5/bin:${PATH}"' >> ~/.profile

rm "$TARBALL"

echo "✅ Python 3.2.5 installed at:"
echo "  $INSTALL_DIR"

echo "✅ Symlink python3.2 in /usr/local/bin"
ln -s /opt/python-3.2.5/bin/python3.2 /usr/local/bin/.

python3.2 --version

# python3.2 -m pip install pyyaml==3.13 --global-option="--without-libyaml"
#
# # sudo apt-get update
# # sudo DEBIAN_FRONTEND=noninteractive apt-get install -y emacs-nox
#
git clone https://github.com/phdye/sqlparse-3.2.5
cd sqlparse-3.2.5
git fetch origin
git checkout 3.2.5
echo ; echo ; echo
python3.2 -m pip install -v .
ln -s /opt/python-3.2.5/bin/sqlformat /usr/local/bin/.
hash -r
which sqlformat
date

#--------------------------------------------------

cat > AGENTS.md <<EOF
# Directives

## AGENTS.md
- Do not store AGENTS.md in the repo.  Treat AGENTS.md as if it were in .gitignore but do not add it to .gitignore.

## Environment - all code you write must be compatible with:
- Python 3.2.5
- Cygwin 1.7.29
- Oracle 12c

## All work must be done from the 3.2.5 branch.
- If the active branch is 'master' or 'work' under 'master', immediately stop and fail.  Do no work that would naturally PR directly to 'master' branch.

## sqlparse
The sqlparse repo is cloned into sqlparse-3.2.5.
The sqlparse package source is in sqlparse-3.2.5/sqlparse.

EOF
