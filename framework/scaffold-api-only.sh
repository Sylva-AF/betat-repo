#!/bin/bash
# scaffold-api-only.sh
# Creates ONLY the per-app api/ sub-packages (common/ already exists, untouched).
# Structural only — directories + empty stubs, no logic, deletes nothing, idempotent.
# DEVELOPER action. Run INSIDE the container, from /workspace/framework, venv active.
set -euo pipefail

if [ ! -d "betat_community" ]; then
    echo "ERROR: run from framework/ (the folder containing betat_community/)."
    echo "You are in: $(pwd)"
    exit 1
fi

cd betat_community

for app in core store communityauth workflow federation bundledui; do
    if [ ! -d "$app" ]; then
        echo "WARN: app '$app' not found — skipping."
        continue
    fi
    mkdir -p $app/api
    touch $app/api/__init__.py
    for f in views serializers mixins; do
        [ -f $app/api/$f.py ] || touch $app/api/$f.py
    done
    echo "created: betat_community/$app/api/ (views, serializers, mixins)"
done

echo ""
echo "Done. Per-app api/ sub-packages created. common/ was not touched."
echo "Notes: api/ folders are plain packages (no apps.py, not in INSTALLED_APPS)."
echo "Existing app-root views.py stays until api/views.py is wired in urls.py."
