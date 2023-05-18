#!/bin/bash

####################################################################################
####################################################################################
#
# THIS SCRIPT WORKS AS A LIB AND SHOULD ONLY BE CALLED FROM ANOTHER SCRIPT
# THERE IS NO REASON TO CALL THIS SCRIPT DIRECTLY
#
####################################################################################
####################################################################################

source ${script_parent}/common/vars.sh

#####################################
# SCRIPT AUXILIARY FUNCTIONS
#####################################
orange_title_message(){
  local message=$1
  printf "\n"
  print_timestamp "${ORANGE}###########################################${NC}"
  print_timestamp "${ORANGE}# $1${NC}"
  print_timestamp "${ORANGE}###########################################\n${NC}"
}

cyan_secondary_message(){
  local message=$1
  printf "\n"
  print_timestamp "${CYAN}********************************************${NC}"
  print_timestamp "${CYAN}* $message${NC}"
  print_timestamp "${CYAN}********************************************\n${NC}"
}

green_secondary_message(){
  local message=$1
  printf "\n"
  print_timestamp "${GREEN}********************************************${NC}"
  print_timestamp "${GREEN}* $message${NC}"
  print_timestamp "${GREEN}********************************************\n${NC}"
}

print_timestamp() {
  local message=$1
  printf "[$(date +'%x %X%Z')] $message \n"
}

get_parent_and_root_dir() {
  local env_file_suffix=$1
  if [ ! -d ${root_dir}/logs ]; then
    mkdir -p ${root_dir}/logs
  fi

  if [ -f ${root_dir}/.env ]; then
    source ${root_dir}/.env
  else
    print_timestamp "${RED}[ERROR] An .env file must exist in ${PURPLE}'${root_dir}' ${RED}directory\n${ORANGE}You can create it running '${script_parent}/setup.sh -s'${NC}"
    exit 1
  fi

  if [ -f ${root_dir}/$env_file_suffix.env ]; then
    source ${root_dir}/$env_file_suffix.env
  else
    print_timestamp "${RED}[ERROR] An $env_file_suffix.env file must exist in ${PURPLE}'${root_dir}' ${RED}directory\n${ORANGE}You can create it running '${script_parent}/setup.sh -s'${NC}"
    exit 1
  fi
}

request_pass() {
  local app=$1
  local pass1=${app}_pass
  local pass2=${app}_pass2
  while :; do
    read -s -p "$app Password: " ${app}_pass >&2
    echo >&2
    read -s -p "Retype $app Password: " ${app}_pass2 >&2
    echo >&2
    if [ "${!pass1}" == "${!pass2}" ]; then
      break
    else
      print_timestamp "${RED}Password must match${NC}" >&2
    fi
  done

  echo ${!pass1}
}

request_user() {
  local app=$1
  local user1=${app}_user
  local user2=${app}_user2
  while :; do
    read -p "$app user: " ${app}_user >&2
    echo >&2
    read -p "Retype $app user: " ${app}_user2 >&2
    echo >&2
    if [ "${!user1}" == "${!user2}" ]; then
      break
    else
      print_timestamp "${RED}Users must match${NC}" >&2
    fi
  done

  echo ${!user1}
}

ask_user () {
    message=$1
    read -p "$message " yn
    echo >&2
    case $yn in
        [Yy]* ) ;;
        [Nn]* ) exit;;
        * ) print_timestamp "Please answer yes or no.";;
    esac
}

#####################################
# OPERATIONAL FUNCTIONS
#####################################

migrate_routine() {
  ${script_parent}/run.sh -c up -r migrate
  local at_migrate_container_name=`docker ps -f name="alphatools_migrate" --format='{{ .Names}}' | awk 'NR==1'`
  if `is_container_running ${at_migrate_container_name}`; then
    local logfile_name="$(date +'%Y%m%d%H%M%Z')migrate.log"
    print_timestamp "Migrate logs are available at ${root_dir}/logs/migrate/${logfile_name}"
    docker ps -a | awk '/alphatools_migrate/ {print "docker logs -f "$1}' | bash -x &> "${root_dir}/logs/migrate/${logfile_name}" &
    print_timestamp "AlphaTools Migrate is running... "
    until [ "`docker ps -a | awk '/alphatools_migrate/ {print \"docker inspect "$1" --format='\''{{ .State.Running}}'\''\"}' | bash -x 2>/dev/null`" = "false" > /dev/null 2>&1 ]; do sleep 1; printf "."; done
    ${script_parent}/run.sh -c down -r migrate
  else
    exit 1
  fi
}

get_secrets(){
  local env_file_suffix=$1
  cyan_secondary_message "Getting environment variables from $env_file_suffix.env file"
  if [ ! -f ${root_dir}/$env_file_suffix.env ]; then
    print_timestamp "${PURPLE}Creating $env_file_suffix.env from template.env ...${NC}"
    cp ${root_dir}/template.env ${root_dir}/$env_file_suffix.env
  fi
}

install_docker() {
  if [ ! "`whoami`" = "root" ];then
    print_timestamp "${RED}You must be root to install Docker, run 'sudo -s' and try again${NC}"
    exit 1
  fi

  if [[ $(cat /proc/version) =~ (ubuntu|debian) ]]; then
    apt-get update
    apt-get -y install apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    apt-get install -y docker-compose-plugin
  fi

  if [[ $(cat /proc/version) =~ "centos" ]]; then
    yum update -y
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    yum install -y docker-compose-plugin
  fi
  systemctl enable docker

#  curl -SL "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o ~/.docker/cli-plugins/docker-compose --create-dirs
#  chmod +x ~/.docker/cli-plugins/docker-compose
}

is_container_running() {
  local container_name=$1
  if [ "`docker container inspect -f '{{.State.Running}}' $container_name`" = 'true' ]; then
    return 0
  else
    return 1
  fi
}