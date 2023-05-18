#!/bin/bash

############################################
# COMMON CONFIGURABLE SCRIPT VARS
############################################

# Setup variables
IS_PRODUCTION='false' #If set to 'true', it will try to retrieve data from Vault with the credentials Below
COMPOSE_VERSION='2.6.0' #https://github.com/docker/compose/releases

############################################
# COMMON FIXED SCRIPT VARS - DO NOT CHANGE
############################################

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0m'
NC='\033[0m' # No Color

# Directories variables
common_parent=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
root_dir=`dirname "${common_parent}"`