#!/bin/bash

script_parent=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source ${script_parent}/common/functions.sh

pre_setup_checks() {
  # Check if docker is installed
  if ! command -v docker &>/dev/null; then
    print_timestamp "${RED}Docker is not installed, please install it before continuing ...${NC}"
    [[ $(cat /proc/version) =~ (centos|ubuntu|debian) ]] && (
      printf "Do you want me to try to install docker for you?"
      ask_user " [y/n]"
      install_docker && green_secondary_message "Docker installed, please run this script again to setup AlphaTools or use the './run.sh' if you want a different setup."
    )
    exit 1
  fi

  # Check if docker-compose is installed
  if ! command -v docker-compose &>/dev/null && ! command -v docker compose &>/dev/null; then
    print_timestamp "${RED}Docker Compose is not installed, please install it before continuing ...${NC}"
    exit 1
  fi

  if systemctl 2>&1 >/dev/null; then
    if (! systemctl --no-pager status docker); then
      systemctl enable docker
      service docker start
      print_timestamp "Waiting Docker to be running ..."
      until [[ "$(systemctl --no-pager status docker)" =~ .*"running".* ]]; do
        sleep 1
        printf "."
      done
      sleep 5
    else
      service docker start
      print_timestamp "Waiting Docker to be running ..."
      until [[ "$(service docker status)" =~ .*"running".* ]]; do
        sleep 1
        printf "."
      done
      sleep 5
    fi
  fi
}

main() {
    ask_user "Do you want to start the setup? [y/n]"
    pre_setup_checks
}

main
