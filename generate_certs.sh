#!/bin/bash
set -e

# Create certs directory if it doesn't exist
mkdir -p certs
cd certs

echo "Generating CA..."
# Generate CA key and certificate
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=MyCustomCA"

echo "Generating Server Certs..."
# Generate Server key and CSR
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"

# Check if subjectAltName config exists, if not create a temporary one
echo "subjectAltName=DNS:localhost,IP:127.0.0.1" > extfile.cnf

# Sign Server Cert with CA
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -extfile extfile.cnf

echo "Generating Client Certs..."
# Generate Client key and CSR
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr -subj "/CN=TestClient"

# Sign Client Cert with CA
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt

# Bundle Client Cert for Browser Import (P12)
openssl pkcs12 -export -out client.p12 -inkey client.key -in client.crt -certfile ca.crt -passout pass:password

# Clean up
rm server.csr client.csr extfile.cnf

echo "Certificates generated in $(pwd)"
echo "Client P12 password is: password"
