#!/bin/bash

red="\033[1;31m"
green="\033[1;32m"
blue="\033[1;34m"
yellow="\033[1;33m"
cyan="\033[1;36m"
white="\033[1;37m"
none="\033[1;0m"
bold="\033[1;1m"


function print_help
{
  echo -e "${yellow}Usage: ./start.sh <client_iface> <server_iface>${none}"
  echo -e "${bold}Example: ./start.sh eth2 eth3${none}"
  exit -1
}

c=$1
s=$2

if [ $# -lt 2 ]
then
  echo -e "${red}Not enough arguments!${none}"
  print_help
elif [ $# -gt 2 ]
then
  echo -e "${red}Too many arguments!${none}"
  print_help
fi

echo -e "${green}Bringing up interfaces with promiscuous mode${none}"
sudo ifconfig $c up promisc
sudo ifconfig $s up promisc

server="sudo python end2end_delay.py server ${s}"
client="sudo python end2end_delay.py client ${c}"

echo -e "${bold}Server mode started in a new xterm${none}"
xterm -geometry 100x1000 -hold -title 'Server' -e $server &

echo -e "${bold}Client mode started in a new xterm${none}"
xterm -geometry 100x1000 -hold -title 'Client' -e $client 





