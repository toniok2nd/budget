#!/usr/bin/env bash
set -e

# Variables
BASE_URL="https://localhost"
CERT="certs/client.crt"
KEY="certs/client.key"
COOKIE_JAR="/tmp/cookies.txt"

# Login as admin
echo "Logging in as admin..."
curl -s -k -c $COOKIE_JAR -b $COOKIE_JAR \
    --cert $CERT --key $KEY \
    -X POST "$BASE_URL/login" \
    -d "username=admin&password=admin" > /dev/null

# Add a transaction (expense by default)
DESC="TestDelete$(date +%s)"
echo "Adding transaction $DESC..."
add_resp=$(curl -s -k -c $COOKIE_JAR -b $COOKIE_JAR \
    --cert $CERT --key $KEY \
    -X POST "$BASE_URL/add" \
    -d "amount=100.00&description=$DESC&category=1")

# Verify transaction appears in history and extract ID
echo "Fetching history to locate transaction..."
history=$(curl -s -k -b $COOKIE_JAR \
    --cert $CERT --key $KEY "$BASE_URL/history")

# Extract the first transaction ID from delete links in history
first_tx_id=$(echo "$history" | grep -oP '/transactions/\K[0-9]+(?=/delete)' | head -n1)
if [ -z "$first_tx_id" ]; then
  echo "Failed to find any transaction ID in history"
  exit 1
fi
TX_ID=$first_tx_id
echo "Found transaction ID: $TX_ID"

# Delete the transaction
echo "Deleting transaction $TX_ID..."
delete_resp=$(curl -s -k -b $COOKIE_JAR \
    --cert $CERT --key $KEY "$BASE_URL/transactions/$TX_ID/delete")

if echo "$delete_resp" | grep -q "Transaction deleted"; then
  echo "Deletion confirmed via flash message."
else
  echo "Deletion flash message not found."
  exit 1
fi

# Verify transaction no longer appears in history
new_history=$(curl -s -k -b $COOKIE_JAR \
    --cert $CERT --key $KEY "$BASE_URL/history")
if echo "$new_history" | grep -q "$DESC"; then
  echo "Transaction still present in history after deletion."
  exit 1
else
  echo "Transaction successfully removed from history."
fi

echo "SUCCESS: Expense mode and transaction deletion verified."
exit 0
