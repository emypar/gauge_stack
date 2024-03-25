#!/bin/bash --noprofile

this_script=${0##*/}

capacity=1024 # MB

case "$0" in
    /*|*/*) this_dir=$(cd $(dirname $0) && pwd);;
    *) this_dir=$(cd $(dirname $(which $0)) && pwd);;
esac
ramfs=ramfs-$(basename $this_dir)

os=$(uname -s)

case "$os" in
    Darwin)
        XXXX=$(($capacity * 2048))
        mount_dir=/Volumes/$ramfs
        if ! diskutil list $mount_dir; then
            diskutil erasevolume HFS+ $ramfs `hdiutil attach -nobrowse -nomount ram://$XXXX` || exit 1
        fi
    ;;
    *) 
        echo >&2 "$this_script - $os: unsupported OS"
        exit 1
    ;;
esac

target_work_dir=$mount_dir/.work
work_dir=$this_dir/.work
mkdir -p $target_work_dir
if [[ "$(readlink $work_dir)" != "$target_work_dir" ]]; then
    (
        set -x
        rm -rf $work_dir.sav
        mv -f $work_dir $work_dir.sav
        ln -fs $target_work_dir $work_dir
    )
fi
ls -al $work_dir


