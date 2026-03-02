#!/bin/bash
##
## Filter library for unified query parsing
## Provides a simple search syntax that translates to SQL or Livestatus
##
## Syntax:
##   value           → search in all searchable fields (LIKE %value%)
##   field:value     → exact match on specific field
##   field:~value    → contains match on specific field
##   field:val1,val2 → multi-value OR (exact match)
##   -field:value    → negation (exclude matches)
##   -value          → negation on all fields
##
## Examples:
##   "SRV-01"              → hostname LIKE '%SRV-01%' OR service LIKE '%SRV-01%' OR ...
##   "hostname:SRV-01"     → hostname = 'SRV-01'
##   "hostname:~SRV"       → hostname LIKE '%SRV%'
##   "state:CRITICAL,DOWN" → state IN ('CRITICAL', 'DOWN')
##   "-state:OK"           → state != 'OK'
##   "-acknowledged"       → (exclude 'acknowledged' in all searchable fields)
##
## Usage:
##   source ./filter.cgi
##
##   # Parse unified query string
##   filter_parse "SRV-01 state:CRITICAL"
##
##   # Or add individual terms
##   filter_add "hostname:SRV-01"
##   filter_add_time_range "$SINCE" "$BEFORE" timestamp
##
##   # Generate SQL (composable)
##   FILTER_SEARCHABLE_FIELDS="hostname service output"
##   filter_to_sql_clauses "hostname service state"
##   FILTER_SQL_CLAUSES+=( "service IS NULL" )   # extra clauses
##   WHERE=$(filter_sql_where)
##
##   # Or generate Livestatus
##   FILTER_SEARCHABLE_FIELDS="host_name description plugin_output"
##   mapfile -t FILTER < <(filter_to_livestatus)
##

# Sanitization patterns by field type
declare -gA FILTER_SANITIZE=(
  [hostname]='[^a-zA-Z0-9._-]'
  [service]='[^a-zA-Z0-9._:/ -]'
  [state]='[^a-zA-Z_,]'
  [state_type]='[^a-zA-Z_,]'
  [contact]='[^a-zA-Z0-9._@-]'
  [command]='[^a-zA-Z0-9._-]'
  [event]='[^a-zA-Z0-9._ -]'
  [output]='[^a-zA-Z0-9._:/ @#!+-]'
  [data]='[^a-zA-Z0-9._:/ @#!+-]'
  [_default]='[^a-zA-Z0-9._:/ @#!+-]'
  [_numeric]='[^0-9]'
)

# Parsed filter entries
# Format: "field|op|value|negate[|ts_field]"
#   field: column name, "_all" for global search, "_time_*" for time ranges
#   op: "=" (exact), "~" (contains), "in" (multi-value), ">=" / "<" (time)
#   value: sanitized value
#   negate: 0 or 1
#   ts_field: timestamp column name (time entries only)
declare -ga FILTER_PARSED=()

# SQL clauses output array (populated by filter_to_sql_clauses)
declare -ga FILTER_SQL_CLAUSES=()

# Searchable fields for _all queries (set by caller before filter_to_*)
declare -g FILTER_SEARCHABLE_FIELDS=""

# --- Sanitization ---

function filter_sanitize() {
  local field=$1 value=$2
  local pattern=${FILTER_SANITIZE[$field]:-${FILTER_SANITIZE[_default]}}
  echo "${value//$pattern/}"
}

function filter_sanitize_numeric() {
  echo "${1//${FILTER_SANITIZE[_numeric]}/}"
}

# --- Parsing ---

## Parse a single filter term and append to FILTER_PARSED
function filter_parse_term() {
  local term=$1
  local negate=0 field="_all" op="~" value

  [[ -z $term ]] && return

  # Negation prefix
  if [[ ${term:0:1} == "-" ]]; then
    negate=1
    term=${term:1}
  fi

  if [[ $term == *:* ]]; then
    # field:value syntax
    field=${term%%:*}
    value=${term#*:}

    if [[ ${value:0:1} == "~" ]]; then
      op="~"
      value=${value:1}
    elif [[ $value == *,* ]]; then
      op="in"
    else
      op="="
    fi
  else
    # No field: global search across all searchable fields
    field="_all"
    op="~"
    value=$term
  fi

  # Sanitize
  if [[ $field == "_all" ]]; then
    value=$(filter_sanitize _default "$value")
  else
    value=$(filter_sanitize "$field" "$value")
  fi

  [[ -z $value ]] && return

  FILTER_PARSED+=( "$field|$op|$value|$negate" )
}

## Reset and parse a full query string (space-separated terms)
function filter_parse() {
  FILTER_PARSED=()
  local terms
  read -ra terms <<< "$1"
  local term
  for term in "${terms[@]}"; do
    filter_parse_term "$term"
  done
}

## Append a single filter term (no reset)
function filter_add() {
  filter_parse_term "$1"
}

## Add time range filters
function filter_add_time_range() {
  local since=$1 before=$2 ts_field=${3:-timestamp}
  since=$(filter_sanitize_numeric "$since")
  before=$(filter_sanitize_numeric "$before")
  [[ $since ]]  && FILTER_PARSED+=( "_time_since|>=|$since|0|$ts_field" )
  [[ $before ]] && FILTER_PARSED+=( "_time_before|<|$before|0|$ts_field" )
}

# --- SQL backend ---

function filter_sql_escape() {
  echo "${1//\'/\'\'}"
}

function filter_sql_in_list() {
  local escaped=$(filter_sql_escape "$1")
  echo "'${escaped//,/\',\'}'"
}

## Populate FILTER_SQL_CLAUSES from FILTER_PARSED
## Usage: filter_to_sql_clauses [valid_fields]
##   valid_fields: space-separated whitelist of allowed field names (optional)
##                 fields not in the list are silently skipped
##                 _all and _time_* entries are always processed
## Requires: FILTER_SEARCHABLE_FIELDS set for _all entries
function filter_to_sql_clauses() {
  local valid_fields=$1
  FILTER_SQL_CLAUSES=()

  local entry field op value negate ts_field

  for entry in "${FILTER_PARSED[@]}"; do
    IFS='|' read -r field op value negate ts_field <<< "$entry"

    # Time range entries
    case $field in
      _time_since)
        FILTER_SQL_CLAUSES+=( "${ts_field:-timestamp} >= datetime($value, 'unixepoch')" )
        continue ;;
      _time_before)
        FILTER_SQL_CLAUSES+=( "${ts_field:-timestamp} < datetime($value, 'unixepoch')" )
        continue ;;
    esac

    # Field whitelist check (skip unknown fields for this table)
    if [[ $valid_fields && $field != "_all" ]]; then
      local _fv_ok=0
      local _fv
      for _fv in $valid_fields; do
        [[ $field == "$_fv" ]] && _fv_ok=1 && break
      done
      (( _fv_ok )) || continue
    fi

    local escaped=$(filter_sql_escape "$value")

    if [[ $field == "_all" ]]; then
      # Global search: LIKE across all searchable fields, combined with OR
      local _or_parts=()
      local _sf
      for _sf in $FILTER_SEARCHABLE_FIELDS; do
        _or_parts+=( "$_sf LIKE '%$escaped%'" )
      done
      if (( ${#_or_parts[@]} > 0 )); then
        local _old_ifs=$IFS
        IFS=$'\x1f'
        local _combined="(${_or_parts[*]})"
        _combined="${_combined//$'\x1f'/ OR }"
        IFS=$_old_ifs
        if (( negate )); then
          FILTER_SQL_CLAUSES+=( "NOT $_combined" )
        else
          FILTER_SQL_CLAUSES+=( "$_combined" )
        fi
      fi
    else
      # Field-specific filter
      case $op in
        "=")
          if (( negate )); then
            FILTER_SQL_CLAUSES+=( "$field != '$escaped'" )
          else
            FILTER_SQL_CLAUSES+=( "$field = '$escaped'" )
          fi ;;
        "~")
          if (( negate )); then
            FILTER_SQL_CLAUSES+=( "$field NOT LIKE '%$escaped%'" )
          else
            FILTER_SQL_CLAUSES+=( "$field LIKE '%$escaped%'" )
          fi ;;
        "in")
          local _in=$(filter_sql_in_list "$value")
          if (( negate )); then
            FILTER_SQL_CLAUSES+=( "$field NOT IN ($_in)" )
          else
            FILTER_SQL_CLAUSES+=( "$field IN ($_in)" )
          fi ;;
      esac
    fi
  done
}

## Join FILTER_SQL_CLAUSES into a "WHERE ..." string
## Returns empty if no clauses
function filter_sql_where() {
  (( ${#FILTER_SQL_CLAUSES[@]} )) || return
  local _old_ifs=$IFS
  IFS=$'\x1f'
  local _result="${FILTER_SQL_CLAUSES[*]}"
  IFS=$_old_ifs
  echo "WHERE ${_result//$'\x1f'/ AND }"
}

# --- Livestatus backend ---

## Convert parsed filters to Livestatus filter directives
## Usage: filter_to_livestatus [valid_fields]
## Requires: FILTER_SEARCHABLE_FIELDS set for _all entries
## Output: Filter directives on stdout (one per line)
function filter_to_livestatus() {
  local valid_fields=$1
  local entry field op value negate ts_field
  local result=()

  for entry in "${FILTER_PARSED[@]}"; do
    IFS='|' read -r field op value negate ts_field <<< "$entry"

    # Time range entries
    case $field in
      _time_since)
        result+=( "Filter: ${ts_field:-last_check} >= $value" )
        continue ;;
      _time_before)
        result+=( "Filter: ${ts_field:-last_check} < $value" )
        continue ;;
    esac

    # Field whitelist check
    if [[ $valid_fields && $field != "_all" ]]; then
      local _fv_ok=0
      local _fv
      for _fv in $valid_fields; do
        [[ $field == "$_fv" ]] && _fv_ok=1 && break
      done
      (( _fv_ok )) || continue
    fi

    if [[ $field == "_all" ]]; then
      local _or_count=0
      local _sf
      for _sf in $FILTER_SEARCHABLE_FIELDS; do
        result+=( "Filter: $_sf ~~ $value" )
        (( _or_count++ ))
      done
      (( _or_count > 1 )) && result+=( "Or: $_or_count" )
      (( negate && _or_count > 0 )) && result+=( "Negate:" )
    else
      case $op in
        "=")
          result+=( "Filter: $field = $value" )
          (( negate )) && result+=( "Negate:" )
          ;;
        "~")
          result+=( "Filter: $field ~~ $value" )
          (( negate )) && result+=( "Negate:" )
          ;;
        "in")
          local _vals _val
          IFS=',' read -ra _vals <<< "$value"
          for _val in "${_vals[@]}"; do
            result+=( "Filter: $field = $_val" )
          done
          (( ${#_vals[@]} > 1 )) && result+=( "Or: ${#_vals[@]}" )
          (( negate )) && result+=( "Negate:" )
          ;;
      esac
    fi
  done

  (( ${#result[@]} )) && printf '%s\n' "${result[@]}"
}

# --- Debug ---

function filter_debug() {
  local entry field op value negate
  echo "=== Parsed Filters (${#FILTER_PARSED[@]}) ===" >&2
  for entry in "${FILTER_PARSED[@]}"; do
    IFS='|' read -r field op value negate <<< "$entry"
    printf "  %-12s %-3s %-20s negate=%s\n" "$field" "$op" "$value" "$negate" >&2
  done
  echo "=== Searchable: $FILTER_SEARCHABLE_FIELDS ===" >&2
}
