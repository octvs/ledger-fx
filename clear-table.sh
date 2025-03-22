#!/bin/sh

# grep: Extract table
# Separate by each row of table
# Remove all html tags
# Remove leading whitespaces
# Remove empty lines

grep "^\s*<tr><td>.*</td></tr>\s*$" \
  | awk -v RS='</td></tr>' '{$1=$1};1' \
  | sed -e 's/<[^>]*>/ /g' \
  | awk '{$1=$1};1' \
  | sed -r '/^\s*$/d'
