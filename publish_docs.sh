#!/bin/bash
set -e # Exit with nonzero exit code if anything fails

TARGET_BRANCH="gh-pages"
GH_PAGES_ROOT="$PWD/docs/build/html"
REPO=`git config remote.origin.url`
SSH_REPO="${REPO/https:\/\/github.com\//git@github.com:}"
SHA=`git rev-parse --verify HEAD`
WD="$PWD"

function doCompile {
  python -m pip install -r docs/requirements.txt
  make -C ./docs html
}

rm -rf "$GH_PAGES_ROOT" || exit 0
git clone "$REPO" "$GH_PAGES_ROOT"
rm -rf "$GH_PAGES_ROOT"/* || exit 0
cd "$GH_PAGES_ROOT"
git checkout --orphan "$TARGET_BRANCH"
touch .nojekyll
cd "$WD"

doCompile

cd "$GH_PAGES_ROOT"

git add -A .
git commit -m "Deploy to GitHub Pages: ${SHA}"
echo "$SSH_REPO" --force "$TARGET_BRANCH"
git push "$SSH_REPO" --force "$TARGET_BRANCH"