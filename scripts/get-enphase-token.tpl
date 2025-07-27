#!/usr/bin/env bash

set -euxo pipefail

COOKIE_FILE="/config/scripts/enphase_cookies.txt"

# 1) Get the login page to capture authenticity_token
TOKEN=$(curl -c "$COOKIE_FILE" -L 'https://enlighten.enphaseenergy.com/login' | sed -n 's/.*name="authenticity_token" value="\([^"]*\)".*/\1/p')

# 2) Log in with the token, email, and password
curl -b "$COOKIE_FILE" -c "$COOKIE_FILE" -X POST 'https://enlighten.enphaseenergy.com/login/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data "utf8=%E2%9C%93&authenticity_token=${TOKEN}&user[email]={{ ENPHASE_EMAIL }}&user[password]={{ ENPHASE_PASSWORD }}" \
  >/dev/null 2>&1

# 3) Fetch the JWT token
jwt_response=$(curl -b "$COOKIE_FILE" 'https://enlighten.enphaseenergy.com/app-api/jwt_token.json' 2>/dev/null)
full_token=$(echo "$jwt_response" | jq -r '.token')

echo "{\"status\":\"OK\",\"token\":\"${full_token}\"}"
