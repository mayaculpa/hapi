#!/bin/env bash

set -eu
readonly LOG_FILE="/tmp/$(basename "$0").log"

info() {
	echo "[INFO][$(date)] $*" | tee -a "$LOG_FILE" >&2 ;
}

error() {
	echo "[ERROR][$(date)] $*" | tee -a "$LOG_FILE" >&2 ;
}

fatal() {
	echo "[FATAL][$(date)] $*" | tee -a "$LOG_FILE" >&2 ; exit 1 ;
}

[[ "$#" -ne 3 ]] && fatal "Usage: $0 <rtu code> <times> <how much>"

thecode="${1:-/tmp/testing}"
howmany="${2:-10}"
howmuch="${3:-10}"

for i in $(seq 1 "$howmany") ; do
	info "[${i}] [EXEC] $thecode $howmuch"
	"$thecode" "$howmuch" > /dev/null 2>&1 || {
		error "[${i}] [FAILED] $thecode $howmuch"
	}
done
