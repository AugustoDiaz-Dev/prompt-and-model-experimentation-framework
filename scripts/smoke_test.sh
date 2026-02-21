#!/usr/bin/env bash
# Smoke test for the Experimentation Framework API.
# Usage: ./scripts/smoke_test.sh [BASE_URL]
# Example: ./scripts/smoke_test.sh http://127.0.0.1:8000

set -e
BASE_URL="${1:-http://127.0.0.1:8000}"

echo "Smoke testing API at $BASE_URL"
echo "---"

# 1. Health
echo -n "GET /health ... "
code=$(curl -s -o /tmp/smoke_body -w "%{http_code}" "$BASE_URL/health")
body=$(cat /tmp/smoke_body)
if [[ "$code" != "200" ]]; then
  echo "FAIL (HTTP $code) $body"
  exit 1
fi
echo "OK ($body)"

# 2. Register prompt
echo -n "POST /prompts ... "
code=$(curl -s -o /tmp/smoke_body -w "%{http_code}" -X POST "$BASE_URL/prompts" \
  -H "Content-Type: application/json" \
  -d '{"name":"smoke_prompt","content":"You are a helpful assistant.","author":"smoke_test"}')
body=$(cat /tmp/smoke_body)
if [[ "$code" != "200" ]]; then
  echo "FAIL (HTTP $code) $body"
  exit 1
fi
echo "OK (prompt registered)"

# 3. List prompts
echo -n "GET /prompts ... "
code=$(curl -s -o /tmp/smoke_body -w "%{http_code}" "$BASE_URL/prompts")
if [[ "$code" != "200" ]]; then
  echo "FAIL (HTTP $code)"
  exit 1
fi
echo "OK"

# 4. Run experiment (inline prompt + minimal test case)
echo -n "POST /experiments ... "
code=$(curl -s -o /tmp/smoke_body -w "%{http_code}" -X POST "$BASE_URL/experiments" \
  -H "Content-Type: application/json" \
  -d '{"name":"smoke_experiment","prompt_content":"Reply with one word: OK","model_name":"gpt-3.5-turbo","test_cases":[{"input":"Test","expected":"OK"}]}')
body=$(cat /tmp/smoke_body)
if [[ "$code" != "200" ]]; then
  echo "FAIL (HTTP $code) $body"
  exit 1
fi
if ! echo "$body" | grep -q '"id"'; then
  echo "FAIL (no id in response) $body"
  exit 1
fi
echo "OK (experiment created)"

echo "---"
echo "All smoke tests passed."
