#!/usr/bin/env ./lib.cgi

[[ -n ${_GET_start//[0-9a-zA-Z\-]} ]] &&
  fatal "bad value for 'start' parameter"
[[ -n ${_GET_end//[0-9z-zA-Z\-]} ]] &&
  fatal "bad value for 'end' parameter"
[[ -n ${_GET_cf//[0-9a-zA-Z]} ]] &&
  fatal "bad value for 'cf' parameter"
[[ -n ${_GET_db//[0-9a-zA-Z\/\-_]} ]] &&
  fatal "bad value for 'db' parameter"
[[ -n ${_GET_ds//[0-9a-zA-Z\-_,]} ]] &&
  fatal "bad value for 'ds' parameter"

start="${_GET_start:--1day}"
start=$(date -d "${start}" +%s)
end="${_GET_end:--now}"
end=$(date -d "${end}" +%s)
step="${_GET_step}"
cf=${_GET_cf:-AVERAGE}
db=${_GET_db}
ds=( ${_GET_ds//,/$IFS} )

[[ -n $db ]] || fatal "empty db name"

OPTS=(
  --no-legend
  --imginfo ""
  --imgformat JSONTIME
  ${start:+--start "$start"}
  ${end:+--end "$end"}
  ${step:+--step $step}
)

BASEDIR=/var/lib/rrd/rrd_perfs
rrdfile=$BASEDIR/$db.rrd

[[ -r $rrdfile ]] || fatal "invalid rrdfile '$rrdfile'"

GRAPH=( )
for ids in "${ds[@]}"; do
  DEF+=( "DEF:$ids=$rrdfile:$ids:$cf" )
done

for ids in "${ds[@]}"; do
  GRAPH+=( "LINE:$ids" )
done

header "Status: 200"
header "Content-Type: application/json; charset=UTF-8"
header ""

exec rrdtool graph - "${OPTS[@]}" "${DEF[@]}" "${GRAPH[@]}"
