#!/usr/bin/env ./lib.cgi
#
# history-availability.cgi - Calculate availability percentage from history
#
# Parameters:
#   hostname - Single mode: exact host. Bulk mode (all=1): contains filter.
#   service  - Single mode: exact service. Bulk mode (all=1): contains filter.
#   query    - Bulk mode: unified filter syntax (see filter.cgi), e.g. "SRV-01",
#              "hostname:~web", "-service:PING". Searches hostname + service.
#   since    - Start timestamp (unix epoch, default: 30 days ago)
#   before   - End timestamp (unix epoch, default: now)
#   period   - Preset time range (overrides since/before): last-24h, yesterday, this-week, etc.
#   all      - If 1, return all host+service combinations (bulk mode)
#   limit    - Bulk mode: max rows returned (optional; omitted = all rows)
#   offset   - Bulk mode: rows to skip (optional, requires limit)
#
# Bulk responses are cached on disk for 5 minutes (dir: KOMPOT_CACHE_DIR,
# default /tmp/kompot-availability-cache) keyed by period/range + filters, so
# the full computation is reused across refreshes and client-side pagination.
#
# Availability calculation:
#   - Available: OK, WARNING, UP states
#   - Unavailable: CRITICAL, DOWN states
#   - Ignored: UNKNOWN, UNREACHABLE states
#   - Result: available / (available + unavailable) * 100
#

source ./filter.cgi

HISTORY_DB=${KOMPOT_HISTORY_DB:-/var/lib/kompot/nagios/nagios-history.db}

[[ -r $HISTORY_DB ]] ||
  fatal "database not found: $HISTORY_DB"

HOSTNAME=${_GET_hostname//[^a-zA-Z0-9._-]}
SERVICE=${_GET_service//[^a-zA-Z0-9._:/ -]}
SINCE=${_GET_since//[^0-9]}
BEFORE=${_GET_before//[^0-9]}
PERIOD=${_GET_period//[^a-z0-9-]}
ALL=${_GET_all//[^01]}
# limit/offset are optional; when omitted, bulk mode returns every matching
# row (the view loads the full set and paginates client-side). The 5-minute
# result cache below keeps that full computation cheap across refreshes.
LIMIT=${_GET_limit//[^0-9]}
OFFSET=${_GET_offset//[^0-9]}
LIMIT_SQL=""
if [[ $LIMIT ]]; then
  LIMIT_SQL="LIMIT $LIMIT"
  [[ $OFFSET ]] && LIMIT_SQL+=" OFFSET $OFFSET"
fi

# Handle period parameter (overrides since/before)
if [[ $PERIOD ]]; then
  if parse_period "$PERIOD"; then
    SINCE=$PERIOD_SINCE
    BEFORE=$PERIOD_BEFORE
  else
    fatal "invalid period '$PERIOD'"
  fi
else
  # Defaults when no period specified
  BEFORE=${BEFORE:-$NOW}
  SINCE=${SINCE:-$(( BEFORE - 30 * 86400 ))}
fi

# Format dates for response
FROM_DATE=$(date -u -d "@$SINCE" +%Y-%m-%dT%H:%M:%SZ)
TO_DATE=$(date -u -d "@$BEFORE" +%Y-%m-%dT%H:%M:%SZ)
TOTAL_PERIOD=$(( BEFORE - SINCE ))

# Bulk mode: all host+service combinations
if [[ $ALL == 1 ]]; then
  # Sanitized query string, reused for both the filter and the cache key.
  Q="${_GET_query//[^a-zA-Z0-9._:\/ @#!,+-]}"

  # 5-minute result cache: the bulk computation is memoized on disk, keyed by
  # the effective request (period/range + filters + limit/offset). Refreshes
  # and client-side pagination within the TTL are served instantly from disk.
  CACHE_TTL=300
  CACHE_DIR=${KOMPOT_CACHE_DIR:-/tmp/kompot-availability-cache}
  CACHE_FILE=""
  if mkdir -p "$CACHE_DIR" 2>/dev/null; then
    CACHE_KEY="${PERIOD:-$SINCE-$BEFORE}|$Q|$HOSTNAME|$SERVICE|$LIMIT|$OFFSET"
    CACHE_HASH=$(printf '%s' "$CACHE_KEY" | md5sum | cut -d' ' -f1)
    CACHE_FILE="$CACHE_DIR/avail-$CACHE_HASH.json"
    if [[ -f $CACHE_FILE ]]; then
      CACHE_AGE=$(( NOW - $(stat -c %Y "$CACHE_FILE") ))
      if (( CACHE_AGE >= 0 && CACHE_AGE < CACHE_TTL )); then
        header "Status: 200"
        header "Content-Type: application/json"
        header "X-Cache: HIT"
        header --send
        cat "$CACHE_FILE"
        exit 0
      fi
    fi
    # Drop expired entries so the cache directory stays bounded.
    find "$CACHE_DIR" -maxdepth 1 -name 'avail-*' -mmin +5 -delete 2>/dev/null
  fi

  # Build optional filters from the unified query syntax shared with the
  # sandbox/history views (see filter.cgi). Legacy hostname/service params are
  # kept as contains-terms for backward compatibility. filter.cgi sanitizes and
  # escapes every value, so the resulting clauses are injection-safe.
  filter_parse "$Q"
  [[ $HOSTNAME ]] && filter_add "hostname:~$HOSTNAME"
  [[ $SERVICE ]]  && filter_add "service:~$SERVICE"
  FILTER_SEARCHABLE_FIELDS="hostname service"
  filter_to_sql_clauses "hostname service"

  # Join the generated clauses with AND so they can be spliced into the CTE and
  # cache WHERE clauses. The time range is handled separately by the view, so
  # no time term is added here.
  BULK_FILTER=""
  for _fc in "${FILTER_SQL_CLAUSES[@]}"; do
    BULK_FILTER+=" AND $_fc"
  done

  # Convert timestamps to dates for cache lookup
  SINCE_DATE=$(date -u -d "@$SINCE" +%Y-%m-%d)
  BEFORE_DATE=$(date -u -d "@$BEFORE" +%Y-%m-%d)

  # Check if cache covers the requested range (excluding today which may be partial)
  TODAY=$(date -u +%Y-%m-%d)
  CACHE_DAYS=$(sqlite3 "$HISTORY_DB" "SELECT COUNT(DISTINCT date) FROM availability_cache WHERE date >= '$SINCE_DATE' AND date < '$BEFORE_DATE' AND date < '$TODAY';" 2>/dev/null || echo 0)
  EXPECTED_DAYS=$(( ($(date -u -d "$BEFORE_DATE" +%s) - $(date -u -d "$SINCE_DATE" +%s)) / 86400 ))
  # Allow for today not being cached
  (( EXPECTED_DAYS > 0 )) && EXPECTED_DAYS=$(( EXPECTED_DAYS - 1 ))

  # Use cache if it covers at least 90% of the expected days
  USE_CACHE=0
  if (( EXPECTED_DAYS > 0 && CACHE_DAYS * 100 / EXPECTED_DAYS >= 90 )); then
    USE_CACHE=1
  fi

  if (( USE_CACHE )); then
    # Fast path: aggregate from cache
    SQL="
SELECT
  hostname, service,
  SUM(available) as available,
  SUM(unavailable) as unavailable,
  SUM(unknown) as unknown,
  CASE
    WHEN SUM(available) + SUM(unavailable) > 0
    THEN ROUND(SUM(available) * 100.0 / (SUM(available) + SUM(unavailable)), 4)
    ELSE 100.0
  END as availability
FROM availability_cache
WHERE date >= '$SINCE_DATE' AND date < '$BEFORE_DATE'$BULK_FILTER
GROUP BY hostname, service
ORDER BY MAX(date) DESC
$LIMIT_SQL;
"
  else
    # Slow path: compute from raw state data
    SQL="
WITH
-- Get distinct host+service combinations that have data in the period
entities AS (
  SELECT hostname, service, MAX(timestamp) as last_change
  FROM state
  WHERE timestamp >= datetime($SINCE, 'unixepoch')
    AND timestamp < datetime($BEFORE, 'unixepoch')
    $BULK_FILTER
  GROUP BY hostname, service
),
-- Get the last state before our time range for each entity
initial_states AS (
  SELECT s.hostname, s.service, s.state, s.timestamp,
         ROW_NUMBER() OVER (PARTITION BY s.hostname, s.service ORDER BY s.timestamp DESC) as rn
  FROM state s
  JOIN entities e ON s.hostname = e.hostname AND s.service IS e.service
  WHERE s.timestamp < datetime($SINCE, 'unixepoch')
),
-- Get all states in our time range
period_states AS (
  SELECT hostname, service, state, timestamp
  FROM state
  WHERE timestamp >= datetime($SINCE, 'unixepoch')
    AND timestamp < datetime($BEFORE, 'unixepoch')
    $BULK_FILTER
),
-- Combine: initial state (clamped to since) + period states
all_states AS (
  SELECT hostname, service, state, datetime($SINCE, 'unixepoch') as timestamp
  FROM initial_states WHERE rn = 1
  UNION ALL
  SELECT hostname, service, state, timestamp FROM period_states
),
-- Add next_timestamp using window function partitioned by entity
state_durations AS (
  SELECT
    hostname, service, state,
    timestamp as start_ts,
    COALESCE(
      LEAD(timestamp) OVER (PARTITION BY hostname, service ORDER BY timestamp),
      datetime($BEFORE, 'unixepoch')
    ) as end_ts
  FROM all_states
),
-- Aggregate durations by entity and category
category_durations AS (
  SELECT
    hostname, service,
    CASE
      WHEN state IN ('OK', 'WARNING', 'UP') THEN 'available'
      WHEN state IN ('CRITICAL', 'DOWN') THEN 'unavailable'
      ELSE 'unknown'
    END as category,
    SUM((julianday(end_ts) - julianday(start_ts)) * 86400) as duration
  FROM state_durations
  GROUP BY hostname, service, category
),
-- Pivot to get available/unavailable/unknown columns per entity
pivoted AS (
  SELECT
    hostname, service,
    COALESCE(SUM(CASE WHEN category = 'available' THEN duration END), 0) as available,
    COALESCE(SUM(CASE WHEN category = 'unavailable' THEN duration END), 0) as unavailable,
    COALESCE(SUM(CASE WHEN category = 'unknown' THEN duration END), 0) as unknown
  FROM category_durations
  GROUP BY hostname, service
)
SELECT
  p.hostname, p.service, p.available, p.unavailable, p.unknown,
  CASE
    WHEN (p.available + p.unavailable) > 0
    THEN ROUND(p.available * 100.0 / (p.available + p.unavailable), 4)
    ELSE 100.0
  END as availability
FROM pivoted p
JOIN entities e ON p.hostname = e.hostname AND p.service IS e.service
ORDER BY e.last_change DESC
$LIMIT_SQL;
"
  fi

  # Build the JSON body into a temp file so it can be cached atomically (mv).
  BODY_TMP=$(mktemp "$CACHE_DIR/avail-tmp-XXXXXX" 2>/dev/null) || BODY_TMP=$(mktemp)
  {
    echo "{"
    echo "  \"from\": \"$FROM_DATE\","
    echo "  \"to\": \"$TO_DATE\","
    echo "  \"total_period\": $TOTAL_PERIOD,"
    echo "  \"cached\": $(if (( USE_CACHE )); then echo "true"; else echo "false"; fi),"
    echo "  \"data\": ["

    first=1
    sqlite3 -separator '|' "$HISTORY_DB" "$SQL" | while IFS='|' read -r host svc avail unavail unk pct; do
      (( first )) || echo ","
      first=0
      svc_json=$(if [[ $svc ]]; then echo "\"$svc\""; else echo "null"; fi)
      # Truncate decimals for integer durations
      avail=${avail%.*}
      unavail=${unavail%.*}
      unk=${unk%.*}
      echo -n "    {\"hostname\":\"$host\",\"service\":$svc_json,\"availability\":$pct,\"available\":${avail:-0},\"unavailable\":${unavail:-0},\"unknown\":${unk:-0}}"
    done

    echo ""
    echo "  ]"
    echo "}"
  } > "$BODY_TMP"

  header "Status: 200"
  header "Content-Type: application/json"
  header "X-Cache: MISS"
  header --send

  # Promote the temp file into the cache (if available), then stream it.
  if [[ $CACHE_FILE ]] && mv -f "$BODY_TMP" "$CACHE_FILE" 2>/dev/null; then
    cat "$CACHE_FILE"
  else
    cat "$BODY_TMP"
    rm -f "$BODY_TMP"
  fi
  exit 0
fi

# Single entity mode
[[ $HOSTNAME ]] || fatal "missing hostname parameter (use all=1 for bulk mode)"

# Build service filter
if [[ $SERVICE ]]; then
  SERVICE_FILTER="AND service = '$SERVICE'"
else
  SERVICE_FILTER="AND service IS NULL"
fi

# SQL to get state durations using window function
read -r -d '' SQL << EOSQL
WITH
-- Get the last state before our time range (to know initial state)
initial_state AS (
  SELECT state, timestamp
  FROM state
  WHERE hostname = '$HOSTNAME'
    $SERVICE_FILTER
    AND timestamp < datetime($SINCE, 'unixepoch')
  ORDER BY timestamp DESC
  LIMIT 1
),
-- Get all states in our time range
period_states AS (
  SELECT state, timestamp
  FROM state
  WHERE hostname = '$HOSTNAME'
    $SERVICE_FILTER
    AND timestamp >= datetime($SINCE, 'unixepoch')
    AND timestamp < datetime($BEFORE, 'unixepoch')
),
-- Combine: initial state (clamped to since) + period states
all_states AS (
  SELECT state, datetime($SINCE, 'unixepoch') as timestamp
  FROM initial_state
  UNION ALL
  SELECT state, timestamp FROM period_states
),
-- Add next_timestamp using window function
state_durations AS (
  SELECT
    state,
    timestamp as start_ts,
    COALESCE(
      LEAD(timestamp) OVER (ORDER BY timestamp),
      datetime($BEFORE, 'unixepoch')
    ) as end_ts
  FROM all_states
)
-- Calculate duration in seconds for each state category
SELECT
  CASE
    WHEN state IN ('OK', 'WARNING', 'UP') THEN 'available'
    WHEN state IN ('CRITICAL', 'DOWN') THEN 'unavailable'
    ELSE 'unknown'
  END as category,
  SUM((julianday(end_ts) - julianday(start_ts)) * 86400) as duration
FROM state_durations
GROUP BY category;
EOSQL

# Execute query and parse results
RESULT=$(sqlite3 -separator '|' "$HISTORY_DB" "$SQL")

# Parse durations
AVAILABLE=0
UNAVAILABLE=0
UNKNOWN=0

while IFS='|' read -r category duration; do
  case $category in
    available)   AVAILABLE=${duration%.*} ;;
    unavailable) UNAVAILABLE=${duration%.*} ;;
    unknown)     UNKNOWN=${duration%.*} ;;
  esac
done <<< "$RESULT"

# Calculate availability percentage
COUNTED=$(( AVAILABLE + UNAVAILABLE ))
if (( COUNTED > 0 )); then
  AVAILABILITY=$(echo "scale=4; $AVAILABLE * 100 / $COUNTED" | bc)
else
  AVAILABILITY="100.0000"
fi

header "Status: 200"
header "Content-Type: application/json"
header --send

cat << EOF
{
  "hostname": "$HOSTNAME",
  "service": $(if [[ $SERVICE ]]; then echo "\"$SERVICE\""; else echo "null"; fi),
  "from": "$FROM_DATE",
  "to": "$TO_DATE",
  "availability": $AVAILABILITY,
  "durations": {
    "available": $AVAILABLE,
    "unavailable": $UNAVAILABLE,
    "unknown": $UNKNOWN,
    "total": $TOTAL_PERIOD
  }
}
EOF
