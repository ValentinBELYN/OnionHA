#!/usr/bin/env bash

# OnionHA
# ~~~~~~~
# Copyright 2017-2020 Valentin BELYN
# GNU General Public License v3.0
# https://github.com/ValentinBELYN/OnionHA


# Compresses the contents of a directory.
# @arg 1: the path of the directory to compress.
# @arg 2: the path of the output file.
compress_dir()
{
  (
    cd $1

    tar --sort=name \
        --owner=root:0 \
        --group=root:0 \
        --mtime=10 \
        -czf ../$2 *
  )
}


# Computes the checksum of a file.
# @arg 1: the path of the file.
# @outputs: the checksum of the file (SHA1).
checksum()
{
  echo $(sha1sum $1 | cut -d ' ' -f 1)
}


# Prints the script header.
header()
{
  echo
  echo '                             /+'
  echo '                             .do.'
  echo '                         .y  ccdy+.'
  echo '                       .yys  -dds+ho.'
  echo '                      -yd/  -hddd:-hh:'
  echo '                      hdh   yddddy odh'
  echo '                      ydd-  yddddy ydy'
  echo '                      `sdh/ :dddh:sdo`'
  echo '                        `/oysydhso/`'
  echo
  echo '≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈'
  echo
  echo '    Onion HA installation file builder'
  echo '    Copyright 2017-2020 Valentin BELYN'
  echo '    GNU General Public License v3.0'
  echo
  echo '≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈'
  echo
}


# Builds the Onion HA installation file.
build()
{
  current_time=$(date +%S)
  waiting_time=$((60 - ${current_time#0}))

  header
  echo 'Waiting time:' $waiting_time 'seconds.'
  echo 'Press Ctrl+C to abort.'
  sleep $waiting_time
  start_time=$(date +%s)

  echo
  echo 'Copying installation files...'
  [[ -d 'onion-ha-setup' ]] && rm -rf onion-ha-setup
  [[ -f 'setup.tar.gz' ]] && rm -f setup.tar.gz

  mkdir onion-ha-setup onion-ha-setup/bin onion-ha-setup/core
  mkdir onion-ha-setup/services onion-ha-setup/config
  cp --no-preserve=all build/oniond.py onion-ha-setup/bin/oniond
  cp --no-preserve=all build/core/*.py onion-ha-setup/core/
  cp --no-preserve=all build/onion-ha.service onion-ha-setup/services/
  cp --no-preserve=all build/oniond.conf onion-ha-setup/config/
  cp --no-preserve=all build/LICENSE onion-ha-setup/
  sleep 1

  echo 'Compressing installation files...'
  compress_dir onion-ha-setup setup.tar.gz
  rm -rf onion-ha-setup

  echo
  tar -tvf setup.tar.gz
  sleep 1

  end_time=$(date +%s)

  echo
  echo 'Checksum:' $(checksum setup.tar.gz)
  echo 'Completed in' $((end_time - start_time)) 'seconds.'
}


build
