#!/system/bin/sh

# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Android shell script to list all subdirectories of a given path since
# "find -type d" is not available on some Android versions.

list_subdirs() {
  for f in "$1"/*
  do
    if [ -d "$f" ]
    then
      if [ "$f" == "." ] || [ "$f" == ".." ]
      then
        continue
      fi
      echo "$f"
      list_subdirs "$f"
    fi
  done
}

list_subdirs "$1"