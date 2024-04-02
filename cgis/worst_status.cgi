#!/usr/bin/env /opt/kompot/www/cgi-bin/lib.cgi

function return_http() {
  header "Status: $1"
  header "Content-Type: plain/text"
  header --send
  echo "$2"
  exit $3
}

function host2svc() {  # convertion du state d'un HOST en state de SERVICE
   #LIVESTATUS nagios :
   #
   #État d'un hôte (Host State) :
   #    0 : UP (Hôte en ligne)
   #    1 : DOWN (Hôte hors ligne)
   #    2 : UNREACHABLE (Hôte injoignable)
   #
   #État d'un service (Service State) :
   #    0 : OK (Service fonctionnant correctement)
   #    1 : WARNING (Service présentant un avertissement)
   #    2 : CRITICAL (Service en état critique)
   #    3 : UNKNOWN (État du service inconnu)
case $1 in
    0) echo 0 ;;
    1) echo 2 ;;
    *) echo 3 ;;
  esac
}

function get_tag_state() {
  tag=$1

  req_host_state="GET hosts\nColumns: name custom_variable_names custom_variable_values custom_variable worst_service_state state\nOutputFormat: csv\nSeparators: 10 9 44 124\n"
  readarray -t array <<< $(echo -e "$req_host_state" | unixcat /var/spool/nagios/cmd/live.sock | awk -F '\t' '$2 ~ /_TAGS/ && $3 ~ /#TATAG/ {print}' )
  host_state=0

  for line in "${array[@]}"; do
      tmp_host_state=$(host2svc $(echo $line | awk '{print $NF}'))
      tmp_svc_state=$(echo $line | awk '{print $(NF-1)}')

      [[ $tmp_host_state -gt $host_state ]] && host_state=$tmp_host_state
      [[ $tmp_svc_state -gt $host_state ]] && host_state=$tmp_svc_state
  done

  req_svc_state="GET services\nColumns: host_alias name custom_variable_names custom_variable_values custom_variable state\nOutputFormat: csv\nSeparators: 10 9 44 124\n"
  readarray -t array <<< $(echo -e "$req_svc_state" | unixcat /var/spool/nagios/cmd/live.sock | awk -F '\t' '$3 ~ /_TAGS/ && $4 ~ /#TATAG/ {print}' )
  svc_state=0

  for line in "${array[@]}"; do
      tmp_state=$(echo $line | awk '{print $NF}')
      [[ $tmp_state -gt $svc_state ]] && svc_state=$tmp_state
  done
  
  [[ $host_state -gt $svc_state ]] && echo $host_state || echo $svc_state
}


unset req_host_state
unset req_svc_state
unset worst_state

if [[ ! -z $_GET_hostname ]] ; then
  if [[ -z $_GET_service ]] ; then	# host state
    req_host_state="GET hosts\nColumns: state\nOutputFormat: csv\nSeparators: 10 9 44 124\nFilter: name = $_GET_hostname"
    req_svc_state="GET hosts\nColumns: worst_service_state\nOutputFormat: csv\nSeparators: 10 9 44 124\nFilter: name = $_GET_hostname"
    name="$_GET_hostname"
  else	# service state
    req_svc_state="GET services\nColumns: state\nOutputFormat: csv\nSeparators: 10 9 44 124\nFilter: host_name = $_GET_hostname\nFilter: description = $_GET_service"
    name="$_GET_hostname/$_GET_service"
  fi
elif [[ ! -z $_GET_hostgroup ]] ; then  # hostgroup state
  req_host_state="GET hostgroups\nColumns: worst_host_state\nOutputFormat: csv\nSeparators: 10 9 44 124\nFilter: name = $_GET_hostgroup\n"
  req_svc_state="GET hostgroups\nColumns: worst_service_state\nOutputFormat: csv\nSeparators: 10 9 44 124\nFilter: name = $_GET_hostgroup\n"
  name="$_GET_hostgroup"
elif [[ ! -z $_GET_servicegroup ]] ; then  # servicegroup state
  req_svc_state="GET servicegroups\nColumns: worst_service_state\nOutputFormat: csv\nSeparators: 10 9 44 124\nFilter: name = $_GET_servicegroup\n"
  name=$_GET_servicegroup  
elif [[ ! -z $_GET_tag ]] ; then  # taged service/host state
  worst_state=$(get_tag_state $_GET_tag)
  name="$_GET_tag"
else
  return_http 400 "bad parameters" 1
fi


if [[ -z $worst_state ]] ; then
  svc_worst_state=$(echo -e "$req_svc_state" | unixcat /var/spool/nagios/cmd/live.sock)
  worst_state=$svc_worst_state
  
  
  if [[ ! -z $req_host_state ]] ; then
    host_worst_state=$(host2svc $(echo -e "$req_host_state" | unixcat /var/spool/nagios/cmd/live.sock))
    [[ $host_worst_state -gt $worst_state ]] && worst_state=$host_worst_state
  fi
fi
  
if [[ -z $worst_state ]]; then
  return_http 500 "livestatus query failed" 1
fi

header "Status: 200"
header "Content-Type: application/json"
header --send
printf '{\n  "name": "%s",\n  "state": %d\n}\n' "$name" "$worst_state"
