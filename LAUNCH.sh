#!/bin/bash

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"
RED="\\033[1;31m"
ROSE="\\033[1;35m"
BLUE="\\033[1;34m"
WHITE="\\033[0;02m"
YELLOW="\\033[1;33m"
CYAN="\\033[1;36m"

. ./D4GENV/bin/activate

isredis=`screen -ls | egrep '[0-9]+.Redis_D4G' | cut -d. -f1`
isflask=`screen -ls | egrep '[0-9]+.Flask_D4G' | cut -d. -f1`

function helptext {
    echo -e $YELLOW"

         _______   __    __                                                                   __
        /       \ /  |  /  |                                                                 /  |
        \$\$\$\$\$\$\$  |\$\$ |  \$\$ |        ______    ______    ______      __   ______    _______  _\$\$ |_
        \$\$ |  \$\$ |\$\$ |__\$\$ |       /      \  /      \  /      \    /  | /      \  /       |/ \$\$   |
        \$\$ |  \$\$ |\$\$    \$\$ |      /\$\$\$\$\$\$  |/\$\$\$\$\$\$  |/\$\$\$\$\$\$  |   \$\$/ /\$\$\$\$\$\$  |/\$\$\$\$\$\$\$/ \$\$\$\$\$\$/
        \$\$ |  \$\$ |\$\$\$\$\$\$\$\$ |      \$\$ |  \$\$ |\$\$ |  \$\$/ \$\$ |  \$\$ |   /  |\$\$    \$\$ |\$\$ |        \$\$ | __
        \$\$ |__\$\$ |      \$\$ |      \$\$ |__\$\$ |\$\$ |      \$\$ \__\$\$ |   \$\$ |\$\$\$\$\$\$\$\$/ \$\$ \_____   \$\$ |/  |
        \$\$    \$\$/       \$\$ |      \$\$    \$\$/ \$\$ |      \$\$    \$\$/    \$\$ |\$\$       |\$\$       |  \$\$  \$\$/
        \$\$\$\$\$\$\$/        \$\$/       \$\$\$\$\$\$\$/  \$\$/        \$\$\$\$\$\$/__   \$\$ | \$\$\$\$\$\$\$/  \$\$\$\$\$\$\$/    \$\$\$\$/
                                  \$\$ |                       /  \__\$\$ |
                                  \$\$ |                       \$\$    \$\$/
                                  \$\$/                         \$\$\$\$\$\$/

    "$DEFAULT"
    This script launch:    (Inside screen Daemons)"$CYAN"
      - All Redis in memory servers.
      - Flask server.

    Usage:    LAUNCH.sh
                  [-l | --launchAuto]
                  [-k | --killAll]
                  [-h | --help]
    "
}

function launching_redis {
    conf_dir="${D4G_HOME}/configs/"
    redis_dir="${D4G_HOME}/redis/src/"

    screen -dmS "Redis_D4G"
    sleep 0.1
    echo -e $GREEN"\t* Launching D4 Redis Servers"$DEFAULT
    screen -S "Redis_D4G" -X screen -t "7201" bash -c $redis_dir'redis-server '$conf_dir'7201.conf ; read x'
    sleep 0.1
}

function shutting_down_redis {
    redis_dir=${D4G_HOME}/redis/src/
    bash -c $redis_dir'redis-cli -p 7201 SHUTDOWN'
    sleep 0.1
}

function checking_redis {
    flag_redis=0
    redis_dir=${D4G_HOME}/redis/src/
    bash -c $redis_dir'redis-cli -p 7201 PING | grep "PONG" &> /dev/null'
    if [ ! $? == 0 ]; then
       echo -e $RED"\t6379 not ready"$DEFAULT
       flag_redis=1
    fi
    sleep 0.1

    return $flag_redis;
}

function launch_redis {
    if [[ ! $isredis ]]; then
        launching_redis;
    else
        echo -e $RED"\t* A D4_Redis screen is already launched"$DEFAULT
    fi
}

function launch_flask {
    if [[ ! $isflask ]]; then
        flask_dir=${D4G_HOME}
        screen -dmS "Flask_D4G"
        sleep 0.1
        echo -e $GREEN"\t* Launching Flask server"$DEFAULT
        screen -S "Flask_D4G" -X screen -t "Flask_server" bash -c "cd $flask_dir; ./Flask_server.py; read x"
    else
        echo -e $RED"\t* A Flask_D4 screen is already launched"$DEFAULT
    fi
}

function killall {


    if [[ $isredis || $isgflask ]]; then
        echo -e $GREEN"\t* Gracefully closing D4G ..."$DEFAULT
        kill $isflask
        echo -e $GREEN"\t* $isflask killed."$DEFAULT
        echo -e $GREEN"\t* Gracefully closing redis servers ..."$DEFAULT
        shutting_down_redis;
        kill $isredis
        sleep 0.2
    else
        echo -e $RED"\t* No screen to kill"$DEFAULT
    fi
}

function update_web {
    echo -e "\t* Updating web..."
    bash -c "(cd ${D4G_HOME}; ./update_web.sh)"
    exitStatus=$?
    if [ $exitStatus -ge 1 ]; then
        echo -e $RED"\t* Web not up-to-date"$DEFAULT
        exit
    else
        echo -e $GREEN"\t* Web updated"$DEFAULT
    fi
}

function launch_all {
    helptext;
    launch_redis;
    launch_flask;
}

#If no params, display the menu
[[ $@ ]] || {

    helptext;

    options=("Redis" "Flask" "Killall" "Update-web")

    menu() {
        echo "What do you want to Launch?:"
        for i in ${!options[@]}; do
            printf "%3d%s) %s\n" $((i+1)) "${choices[i]:- }" "${options[i]}"
        done
        [[ "$msg" ]] && echo "$msg"; :
    }

    prompt="Check an option (again to uncheck, ENTER when done): "
    while menu && read -rp "$prompt" numinput && [[ "$numinput" ]]; do
        for num in $numinput; do
            [[ "$num" != *[![:digit:]]* ]] && (( num > 0 && num <= ${#options[@]} )) || {
                msg="Invalid option: $num"; break
            }
            ((num--)); msg="${options[num]} was ${choices[num]:+un}checked"
            [[ "${choices[num]}" ]] && choices[num]="" || choices[num]="+"
        done
    done

    for i in ${!options[@]}; do
        if [[ "${choices[i]}" ]]; then
            case ${options[i]} in
                Redis)
                    launch_redis
                    ;;
                Flask)
                    launch_flask;
                    ;;
                Killall)
                    killall;
                    ;;
                Update-web)
                    update_web;
                    ;;
            esac
        fi
    done

    exit
}

while [ "$1" != "" ]; do
    case $1 in
        -l | --launchAuto )         launch_all;
                                    ;;
        -k | --killAll )            helptext;
                                    killall;
                                    ;;
        -h | --help )               helptext;
                                    exit
                                    ;;
        * )                         helptext
                                    exit 1
    esac
    shift
done
