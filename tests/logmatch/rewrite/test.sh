#!/bin/bash
curdir=${0%/*}

echo 'Testing logmatch rewrites'

diff -u --color=auto "$curdir/expect" <(
    "${LOGMATCH_BIN:-logmatch}" -b \
        -v "CONFIG=$curdir/logmatch.conf" \
        -v "ALIASES=$curdir/aliases.conf" \
        -v NAGIOS_EXTERNAL_COMMAND_FILE=/dev/stdout \
        < "$curdir/input" |
            sed -r -e '/^OK$/d' \
                -e 's,^\[[0-9]+\](\s+PROCESS_SERVICE_CHECK_RESULT),[0]\1,'
)
