#!/usr/bin/env bash
# load.sh - Load shell locale strings based on PLUGIN_LANG in .env
# Usage: source "$(dirname "$0")/i18n/load.sh"

_I18N_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"

_PLUGIN_LANG="en"
if [ -f "$_DATA_DIR/.env" ]; then
  _LANG_VAL=$(grep '^PLUGIN_LANG=' "$_DATA_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  [ -n "$_LANG_VAL" ] && _PLUGIN_LANG="$_LANG_VAL"
fi

# Map zh-TW to zh_TW for filename
_LANG_FILE="${_PLUGIN_LANG//-/_}"

if [ -f "$_I18N_DIR/${_LANG_FILE}.sh" ]; then
  source "$_I18N_DIR/${_LANG_FILE}.sh"
else
  source "$_I18N_DIR/en.sh"
fi
