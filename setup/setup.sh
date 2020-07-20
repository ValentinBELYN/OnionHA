#!/usr/bin/env bash

# OnionHA
# ~~~~~~~
# Copyright 2017-2020 Valentin BELYN
# GNU General Public License v3.0
# https://github.com/ValentinBELYN/OnionHA


readonly ONION_VERSION='2.0.1'
readonly ONION_BIN_FILE='/usr/local/bin/oniond'
readonly ONION_SERVICE_FILE='/etc/systemd/system/onion-ha.service'
readonly ONION_LIB_DIR='/usr/local/lib/onion-ha/'
readonly ONION_CORE_DIR='/usr/local/lib/onion-ha/oniond/'
readonly ONION_CONF_DIR='/etc/onion-ha/'
readonly SETUP_FILE='setup.tar.gz'
readonly SETUP_HASH='ae972f75bae78c200350a4b94e53091bbda5385f'
readonly SETUP_TEMP_DIR='/tmp/onion-ha-setup/'


# Indicates whether the current user has root privileges.
# @returns 0 if the user is root, 1 otherwise.
is_root()
{
  [[ $EUID -eq 0 ]]
}


# Indicates whether the specified command is installed on the system.
# @arg 1: the name of the command.
# @returns: 0 if the command exists, 1 otherwise.
is_installed()
{
  type -p $1 > /dev/null
}


# Indicates whether the current device is connected to the Internet.
# @returns: 0 if the connection is operational, 1 otherwise.
is_connected()
{
  ping -c 1 -W 1 one.one.one.one > /dev/null 2>&1
}


# Searches an input string for a substring that matches a regular
# expression pattern.
# @arg 1: the string to search for a match.
# @arg 2: the regular expression pattern to match.
# @outputs: the first occurrence found.
# @returns: 0 if the pattern is not found in the string, 1 otherwise.
regex_match()
{
  local string=$1
  local pattern=$2

  [[ $string =~ $pattern ]] && echo ${BASH_REMATCH[2]}
}


# Gets the current version of Python.
# @outputs: the version of Python installed on the system.
get_python_version()
{
  local string=$(python3 --version)
  local pattern='^(.* ([0-9.]*))$'

  echo $(regex_match "$string" "$pattern")
}


# Gets the current version of Onion HA.
# @outputs: the version of Onion HA installed on the system.
get_oniond_version()
{
  local string=$(oniond version)
  local pattern='^(.* ([0-9.]*) .*)$'

  echo $(regex_match "$string" "$pattern")
}


# Computes the checksum of a file.
# @arg 1: the path of the file.
# @outputs: the checksum of the file (SHA1).
checksum()
{
  echo $(sha1sum $1 | cut -d ' ' -f 1)
}


# Asks the user for confirmation before continuing.
# @arg 1: the message to display.
# @returns: 0 if the user wants to continue, 1 otherwise.
ask()
{
  local prompt=$1
  local answer

  echo
  read -r -p "$1 [Y/n] " answer

  [[ $answer =~ ^[Yy]([Ee][Ss])?$ ]]
}


# Displays and animates a message.
# @args: the message to display.
animate()
{
  local string=$@
  local length=${#string}

  for (( i = 0; i < length; i++ )); do
    echo -n "${string:$i:1}"
    sleep 0.05
  done

  echo
}


# Displays an error and exits the script.
# @args: the error to display.
error()
{
  echo 'Error:' $@
  exit 1
}


# Exits the script.
cancel()
{
  echo 'Canceled.'
  exit
}


# Prepares and extracts files for installation.
prepare()
{
  mkdir $SETUP_TEMP_DIR
  tar -xzf $SETUP_FILE -C $SETUP_TEMP_DIR
}


# Cleans up installation files.
clean()
{
  rm -rf $SETUP_TEMP_DIR
}


# Installs and updates the libraries required by Onion HA.
install_libraries()
{
  pip3 install --upgrade icmplib
  pip3 install --upgrade configpilot
}


# Installs Onion HA on the system.
install_onion_core()
{
  mkdir -p $ONION_CORE_DIR

  cp $SETUP_TEMP_DIR/core/* $ONION_CORE_DIR
  cp $SETUP_TEMP_DIR/bin/oniond $ONION_BIN_FILE
  cp $SETUP_TEMP_DIR/services/onion-ha.service $ONION_SERVICE_FILE

  chmod +x $ONION_BIN_FILE

  systemctl daemon-reload
  systemctl enable onion-ha
}


# Removes Onion HA from the system.
remove_onion_core()
{
  systemctl stop onion-ha
  systemctl disable onion-ha

  rm -f $ONION_BIN_FILE
  rm -f $ONION_SERVICE_FILE
  rm -rf $ONION_LIB_DIR

  systemctl daemon-reload
}


# Installs the default configuration of Onion HA.
install_config()
{
  mkdir -p $ONION_CONF_DIR/actions
  cp $SETUP_TEMP_DIR/config/oniond.conf $ONION_CONF_DIR
}


# Removes the current configuration of Onion HA.
remove_config()
{
  rm -rf $ONION_CONF_DIR
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
  echo '    Onion HA' $ONION_VERSION
  echo '    Copyright 2017-2020 Valentin BELYN'
  echo '    GNU General Public License v3.0'
  echo
  echo '≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈'
  echo
}


# Prints how to use this script.
usage()
{
  echo 'Usage: setup.sh [command]'
  echo
  echo 'Commands:'
  echo '    install         Install Onion HA on this server'
  echo '    update          Update Onion HA to the latest version'
  echo '    remove          Remove Onion HA and delete the configuration'
  echo '    help            Show this help message'
  exit
}


# Installs Onion HA on this server.
# This function is interactive and asks the user for confirmation.
install()
{
  if is_installed oniond; then
    error 'Onion HA' $(get_oniond_version) 'is already installed.'
  fi

  echo 'You are ready to install Onion HA on this server.'
  echo 'You will need to be connected to the Internet during the process.'

  if ! ask 'Do you want to install Onion HA?'; then
    cancel
  fi

  echo 'Installing...'
  {
    prepare
    install_libraries
    install_onion_core
    install_config
    clean

  } > /dev/null 2>&1

  echo
  animate 'Onion HA was successfully installed.'
  animate 'If you like Onion HA, please support us on GitHub or make a' \
          'donation!'
  echo '    https://github.com/ValentinBELYN/OnionHA'
}


# Updates Onion HA to the latest version.
# This function is interactive and asks the user for confirmation.
update()
{
  if ! is_installed oniond; then
    error 'Onion HA is not installed on this server.'
  fi

  local current_version=$(get_oniond_version)

  if [[ ! $current_version < $ONION_VERSION ]]; then
    error 'Onion HA is already up to date! (' $current_version ')'
  fi

  echo 'You are ready to update Onion HA on this server.'
  echo 'You will need to be connected to the Internet during the process.'
  echo
  echo 'Warning'
  echo '-------'
  echo '  - Onion HA will be stopped. You will need to restart it after' \
       'the update.'
  echo '  - Your current configuration will be kept.'

  if ! ask 'Do you want to update Onion HA?'; then
    cancel
  fi

  echo 'Updating...'
  {
    prepare
    install_libraries
    remove_onion_core
    install_onion_core
    clean

  } > /dev/null 2>&1

  echo
  animate 'Onion HA is now up to date.'
  animate 'If you like Onion HA, please support us on GitHub or make a' \
          'donation!'
  echo '    https://github.com/ValentinBELYN/OnionHA'
}


# Removes Onion HA and deletes the configuration.
# This function is interactive and asks the user for confirmation.
remove()
{
  if ! is_installed oniond; then
    error 'Onion HA is not installed on this server.'
  fi

  echo 'You are ready to remove Onion HA from this server.'
  echo
  echo 'Warning'
  echo '-------'
  echo '  - Onion HA will be stopped.'
  echo '  - Your current configuration will be DELETED.'

  if ! ask 'Do you want to remove Onion HA?'; then
    cancel
  fi

  echo 'Removing...'
  {
    remove_onion_core
    remove_config

  } > /dev/null 2>&1

  echo
  animate 'Onion HA was successfully removed.'
  animate 'Leave a comment on GitHub to help us improve Onion HA.'
  echo '    https://github.com/ValentinBELYN/OnionHA'
}


# Prerequisite checks.
if [[ $# -lt 1 || ! $1 =~ ^(install|update|remove)$ ]]; then
  usage

elif [[ ! -f $SETUP_FILE || $(checksum $SETUP_FILE) != $SETUP_HASH ]]; then
  error 'unable to read the installation file.'

elif ! is_root; then
  error 'this script does not have enough privileges to start.'

elif ! is_installed python3 || [[ $(get_python_version) < '3.6' ]]; then
  error 'Onion HA requires Python 3.6 or higher.'

elif ! is_installed pip3; then
  error 'this script requires pip3 to continue.'

elif ! is_connected; then
  error 'this script needs to be connected to the Internet to continue.'

else
  header
  $1
  echo
fi
