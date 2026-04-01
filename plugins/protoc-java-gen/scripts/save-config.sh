#!/usr/bin/env bash
# save-config.sh - Save protoc-java-gen configuration
# Usage: bash save-config.sh [protoc_path] [project_root] [proto_dir] [lang]
#   Pass "skip" or "-" to keep the existing value for any argument.
#   proto_dir: relative to project_root, default "proto"
#   lang: en or zh-TW, default en

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/protoc-java-gen"
ENV_FILE="$DATA_DIR/.env"

source "$(dirname "$0")/i18n/load.sh"

mkdir -p "$DATA_DIR"

# Normalize "skip" / "-" to empty string
[ "$1" = "skip" ] || [ "$1" = "-" ] && set -- "" "${@:2}"
[ "$2" = "skip" ] || [ "$2" = "-" ] && set -- "$1" "" "${@:3}"
[ "$3" = "skip" ] || [ "$3" = "-" ] && set -- "$1" "$2" "" "$4"
[ "$4" = "skip" ] || [ "$4" = "-" ] && set -- "$1" "$2" "$3" ""

PROTOC_PATH=$(resolve_arg "$1" PROTOC_PATH "")
PROJECT_ROOT=$(resolve_arg "$2" PROJECT_ROOT "")
PROTO_DIR=$(resolve_arg "$3" PROTO_DIR "proto")
PLUGIN_LANG=$(resolve_arg "$4" PLUGIN_LANG "en")

printf 'PROTOC_PATH=%s\nPROJECT_ROOT=%s\nPROTO_DIR=%s\nPLUGIN_LANG=%s\n' \
  "$PROTOC_PATH" "$PROJECT_ROOT" "$PROTO_DIR" "$PLUGIN_LANG" > "$ENV_FILE"
chmod 600 "$ENV_FILE"

_msg="${MSG_CONFIG_SAVED//%PROTOC_PATH%/$PROTOC_PATH}"
_msg="${_msg//%PROJECT_ROOT%/$PROJECT_ROOT}"
_msg="${_msg//%PROTO_DIR%/$PROTO_DIR}"
_msg="${_msg//%LANG%/$PLUGIN_LANG}"
echo "$_msg"
