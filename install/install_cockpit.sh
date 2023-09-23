#!/bin/bash
# Define PATH
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
# Export PATH
export PATH


## This script is used for install or upgrade Cockpit on Linux
## Cockpit build at redhat family: https://copr.fedorainfracloud.org/coprs/g/cockpit/cockpit-preview/monitor/
## PackageKit: https://www.freedesktop.org/software/PackageKit/
## Not use pkcon install/update cockpit, the reason is: https://cockpit-project.org/faq.html#error-message-about-being-offline
## pkcon can read repositories at you system directly, it don't provide exra repository
## [apt show cockpit] or [apt install cockpit] show all additional packages
## Ubuntu have backports at file /etc/apt/sources.list by default
## Cockpit application: https://cockpit-project.org/applications

# Command-line options
# ==========================================================
#
# --port <9000>
# Use the --port option to set Websoft9 cosole port. default is 9000, for example:
#
#   $ sudo sh install_cockpit.sh --port 9001



############################################################
# Below vars export from install.sh
#  $cockpit_port
#  $install_path
############################################################

# 设置参数的默认值
port="9000"

# 获取参数值
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            port="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done


if [ -z "$cockpit_port" ]; then
  cockpit_port=$port
fi

echo_prefix_cockpit=$'\n[Cockpit] - '
cockpit_packages_install="cockpit cockpit-pcp cockpit-sosreport"
cockpit_packages_upgrade="cockpit cockpit-ws cockpit-bridge cockpit-system cockpit-ws cockpit-storaged cockpit-session-recording  cockpit-doc cockpit-packagekit cockpit-pcp cockpit-sosreport"
cockpit_plugin_delete="apps,machines,selinux,subscriptions,kdump,updates,playground,packagekit"
menu_overrides_github_page_url="https://websoft9.github.io/websoft9/cockpit/menu_override"
cockpit_config_github_page_url="https://websoft9.github.io/websoft9/cockpit/cockpit.conf"
cockpit_menu_overrides=(networkmanager.override.json shell.override.json storaged.override.json systemd.override.json users.override.json)
# export OS release environments
if [ -f /etc/os-release ]; then
    . /etc/os-release
else
    echo "Can't judge your Linux distribution"
    exit 1
fi

# This solution from: https://help.ubuntu.com/community/PinningHowto
pin_config="
Package: cockpit*
Pin: release a=$VERSION_CODENAME-backports
Pin-Priority: 1000
"

check_ports() {
    local ports=("$@")

    for port in "${ports[@]}"; do
        if netstat -tuln | grep ":$port " >/dev/null; then
            echo "Port $port is in use, install failed"
            exit
        fi
    done

    echo "All ports are available"
}

Print_Version(){

    if command -v apt >/dev/null; then
        apt show cockpit | head -n 15
    else
        yum info cockpit || dnf info cockpit
    fi

}

Install_PackageKit(){
    echo "$echo_prefix_cockpit Install PackageKit(pkcon) and Cockpit repository"

    if command -v pkcon &> /dev/null; then
        echo "pkcon is at your system ..."

    elif command -v yum &> /dev/null; then
        if [ "$(cat /etc/redhat-release)" = "Redhat7" ]; then
            sudo subscription-manager repos --enable rhel-7-server-extras-rpms
        fi
        sudo yum install PackageKit

    elif command -v dnf &> /dev/null; then
        sudo dnf install PackageKit

    elif command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install packagekit

    else
        echo "PackageKit not found, Cockpit cannot be installed"
        exit 1
    fi
}


Set_Repository() {
    echo "$echo_prefix_cockpit Set Cockpit repository"
    if command -v apt &> /dev/null; then
        if [ "$NAME" = "Debian" ]; then
            echo "deb http://deb.debian.org/debian $VERSION_CODENAME-backports main" > /etc/apt/sources.list.d/backports.list
        fi
        echo "Set the cockpit repository priority on Ubuntu/Debian..."
        sudo bash -c "echo '$pin_config' > /etc/apt/preferences.d/cockpit_backports"
    fi
    echo "Complete set Cockpit repository"
}


Restart_Cockpit(){
    echo "$echo_prefix_cockpit Restart Cockpit"
    sudo systemctl daemon-reload
    sudo systemctl restart cockpit
    sudo systemctl restart cockpit.socket
}

Set_Firewall(){
  echo "$echo_prefix_cockpit Set firewall for cockpit access"
  if command -v firewall-cmd &> /dev/null; then
     echo "Set firewall for Cockpit..."
     sudo firewall-cmd --permanent --zone=public --add-service=cockpit
     sudo firewall-cmd --reload
  fi

  if [ -f /etc/selinux/config ]; then
     echo "Set Selinux for Cockpit..."
     sudo setenforce 0  1>/dev/null 2>&1
     sudo sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config  1>/dev/null 2>&1
  fi
}

Set_Cockpit(){
    echo "$echo_prefix_cockpit Set Cockpit for Websoft9"

    echo "Cockpit allowed root user ..." 
    echo "" > /etc/cockpit/disallowed-users

    # fix bug: https://github.com/Websoft9/websoft9/issues/332
    sed 's/selector(:is():where())/selector(:is(*):where(*))/' -i /usr/share/cockpit/static/login.js 

    echo "Set Cockpit config file..." 
    if [ -f "$install_path/cockpit/cockpit.conf" ]; then
        cp -f "$install_path/cockpit/cockpit.conf" /etc/cockpit/cockpit.conf
    else
        echo "Download config from URL $cockpit_config_github_page_url"
        curl -sSL $cockpit_config_github_page_url | sudo tee /etc/cockpit/cockpit.conf > /dev/null
    fi

    echo "Change cockpit default port to $cockpit_port ..." 
    sudo sed -i "s/ListenStream=9090/ListenStream=$cockpit_port/" /lib/systemd/system/cockpit.socket


    # fwupd-refresh.service may push error for Cockpit menu, so disable it
    if sudo systemctl is-active --quiet fwupd-refresh.service; then
        echo "fwupd-refresh.service is already running. Stopping and disabling it..."
        sudo systemctl stop fwupd-refresh.service
        sudo systemctl disable fwupd-refresh.service
        echo "fwupd-refresh.service stopped and disabled."
    else
        echo "fwupd-refresh.service is not running."
    fi

}

Download_Menu_Override(){
    for file in "${cockpit_menu_overrides[@]}"
        do

        echo "$menu_overrides_github_page_url/$file"

        curl -sSL "$menu_overrides_github_page_url/$file" | sudo tee /etc/cockpit/"$file" > /dev/null
        if [ $? -ne 0 ]; then
        echo "Failed to download files"
        exit 1
        fi

        done
}

Edit_Menu(){
    echo "$echo_prefix_cockpit Start to edit Cockpit origin Menu"
    if [ -f "$install_path/cockpit/cockpit.conf" ]; then
        cp -f "$install_path/cockpit/cockpit.conf" /etc/cockpit/cockpit.conf
    else
        echo "Download config file from URL..."
        curl -sSL $cockpit_config_github_page_url | sudo tee /etc/cockpit/cockpit.conf > /dev/null
    fi

    if test -d "$install_path/cockpit/menu_override"; then
        cp -r $install_path/cockpit/menu_override/* /etc/cockpit
    else
        echo "Download override files from URL..."
        Download_Menu_Override
    fi

    echo "$cockpit_plugin_delete" | tr ',' '\n' | sudo xargs -I {} rm -rf "/usr/share/cockpit/{}"
}

Upgrade_Cockpit(){
    echo "$echo_prefix_cockpit Prepare to upgrade Cockpit"
    echo "You installed version:  "
    Print_Version
    if command -v apt >/dev/null; then
        export DEBIAN_FRONTEND=noninteractive
        sudo dpkg --configure -a
        apt update -y
        apt --fix-broken install
        apt install -u $cockpit_packages_upgrade -y
    else
        sudo pkcon refresh > /dev/null
        sudo pkcon get-updates > /dev/null
        sudo pkcon update $cockpit_packages_upgrade -y
    fi
}

Install_Cockpit(){

    if systemctl list-unit-files | grep -q cockpit.service; then
        Upgrade_Cockpit
        Restart_Cockpit
    else
        echo "$echo_prefix_cockpit Prepare to install Cockpit" 
        check_ports $port
        export DEBIAN_FRONTEND=noninteractive
        sudo pkcon refresh > /dev/null
        sudo pkcon get-updates > /dev/null
        sudo pkcon install $cockpit_packages_install -y --allow-untrusted
        Restart_Cockpit
    fi

    Set_Firewall
    Set_Cockpit
    Edit_Menu
    Restart_Cockpit
}

Test_Cockpit(){
    echo "$echo_prefix_cockpit Test Cockpit console accessibility" 
    test_cmd="curl localhost:$cockpit_port"

    if $test_cmd >/dev/null 2>&1; then
        echo "Cockpit running OK..."
    else
        echo "Cockpit is not running..."
        exit 1
    fi

    Print_Version
}


#### -------------- main() start here  -------------------  ####

Install_PackageKit
Set_Repository
Install_Cockpit
Test_Cockpit

# release package memory
sudo systemctl restart packagekit.service