#!/usr/bin/env bash
# Recreate the authoring machine's layout on a GitHub runner: /home/claude/{fb,rs,doc}. Usage: setup.sh "<footage folders...>"
set -euo pipefail
WS="$GITHUB_WORKSPACE"; export DEBIAN_FRONTEND=noninteractive
sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /opt/hostedtoolcache/CodeQL || true
for i in 1 2 3 4; do
  timeout 420 sudo -E apt-get -o DPkg::Lock::Timeout=300 -o Acquire::Retries=3 update -qq && \
  timeout 600 sudo -E apt-get -o DPkg::Lock::Timeout=300 -o Acquire::Retries=3 install -y -qq --no-install-recommends ffmpeg fonts-inter fonts-dejavu-core >/dev/null && break
  echo "apt retry $i"; sleep 20
done
which ffmpeg
pip install -q numpy scipy pillow soundfile
sudo mkdir -p /home/claude && sudo chown "$(id -u):$(id -g)" /home/claude
ln -sfn "$WS" /home/claude/rs
git clone -q --depth 1 --filter=blob:none --sparse --branch footage "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" /home/claude/fb
(cd /home/claude/fb && git sparse-checkout set $1)
python3 "$WS/ci/chiricahua/unpack.py" /home/claude/doc/runner
python3 "$WS/ci/chiricahua/patch_plan.py" /home/claude/doc/runner/chiricahua/plan_v2.py
cp -r /home/claude/doc/runner/chiricahua /home/claude/doc/chiricahua
cp -r /home/claude/doc/runner/geo /home/claude/doc/geo
python3 /home/claude/doc/runner/prepare.py
ffmpeg -version | head -1; fc-list | grep -c -i inter; df -h / | tail -1
