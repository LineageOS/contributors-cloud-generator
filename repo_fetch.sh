#!/bin/bash

GIT_CMD=/usr/bin/git

OLD_PWD=`pwd`
REPO_DIR=$OLD_PWD/db/repos/$1.git
STATS_DIR=$OLD_PWD/db/stats/$1

echo "REPO: $REPO_DIR"
if [ ! -d "$REPO_DIR" ]; then
    git clone --bare https://github.com/$1.git $REPO_DIR
fi
$GIT_CMD --bare --git-dir=$REPO_DIR fetch -p origin '+refs/heads/*:refs/heads/*'

# Get repository stats
mkdir -p $STATS_DIR
$GIT_CMD --bare --git-dir=$REPO_DIR shortlog -e -s -n --all > $STATS_DIR/all_stats.dat
$GIT_CMD --bare --git-dir=$REPO_DIR shortlog -e -s -n --all --grep='Automatic translation import' > $STATS_DIR/translations_stats.dat

cd $OLD_PWD
