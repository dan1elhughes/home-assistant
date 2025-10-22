#!/usr/bin/env bash
# Fetch Enphase schedule IDs grouped by type (CFG/DTG/RBD) for Home Assistant.
# Uses ENPHASE_AUTH (JWT) and ENPHASE_XSRF (xsrf) environment variables.

set -uo pipefail

SITE_ID="{{ ENPHASE_BATTERY_ID }}"
USERNAME="{{ ENPHASE_USER_ID }}"
LOG_FILE="/config/scripts/enphase_schedules.log"

{
  echo
  echo "========== $(date '+%F %T') =========="
  echo "Script started"
  echo "AUTH present: $([ -n "${ENPHASE_AUTH:-}" ] && echo yes || echo no), XSRF: ${ENPHASE_XSRF:-missing}"
} >> "$LOG_FILE"

if [[ -z "${ENPHASE_AUTH:-}" || -z "${ENPHASE_XSRF:-}" ]]; then
  echo '{"error":"Missing or empty tokens"}'
  echo "Missing or empty tokens" >> "$LOG_FILE"
  exit 0
fi

BASE_URL="https://enlighten.enphaseenergy.com/service/batteryConfig/api/v1/battery/sites/${SITE_ID}"

JSON=$(curl -sS "${BASE_URL}/schedules" \
  -H "accept: application/json, text/plain, */*" \
  -H "content-type: application/json" \
  -H "origin: https://battery-profile-ui.enphaseenergy.com" \
  -H "referer: https://battery-profile-ui.enphaseenergy.com/" \
  -H "username: ${USERNAME}" \
  -H "x-xsrf-token: ${ENPHASE_XSRF}" \
  -H "e-auth-token: ${ENPHASE_AUTH}" 2>>"$LOG_FILE" || echo "")

{% raw %}
echo "Raw response length: ${#JSON}" >> "$LOG_FILE"
{% endraw %}

if [[ -z "$JSON" ]]; then
  echo '{"error":"Empty response from API"}'
  echo "Empty API response" >> "$LOG_FILE"
  exit 0
fi

if ! echo "$JSON" | jq empty >/dev/null 2>&1; then
  SHORT=$(echo "$JSON" | head -c 200 | sed 's/"/\\"/g')
  echo "{\"error\":\"Invalid or non-JSON response\",\"preview\":\"${SHORT}...\"}"
  echo "Invalid JSON: ${SHORT}" >> "$LOG_FILE"
  exit 0
fi

OUTPUT=$(echo "$JSON" | jq -c '{
  cfg: (.cfg.details // [] | map(.scheduleId)),
  dtg: (.dtg.details // [] | map(.scheduleId)),
  rbd: (.rbd.details // [] | map(.scheduleId)),
  other: []
}')

echo "$OUTPUT"
echo "Output: $OUTPUT" >> "$LOG_FILE"
exit 0
