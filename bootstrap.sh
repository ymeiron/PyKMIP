#!/bin/bash
dir="$1"

if [ -e "$dir" ]; then
  echo "Error: directory already exists"
fi

client_name="gandalf"

mkdir -p "$dir/ca"
mkdir -p "$dir/clients"
mkdir -p "$dir/server"

openssl req -x509 -new -nodes -sha256 -days 3652 -out "$dir/ca/ca-cert.pem" -keyout "$dir/ca/ca-privkey.pem" -addext "keyUsage=critical,digitalSignature,keyCertSign" -subj "/CN=PyKMIP Root CA/"

ln -s "$dir/ca/ca-cert.pem" "$dir/server/"

openssl req -new -newkey rsa:2048 -nodes -subj "/CN=server/" -keyout "$dir/server/server-privkey.pem" | openssl x509 -req -sha256 -CA "$dir/ca/ca-cert.pem" -CAkey "$dir/ca/ca-privkey.pem" -out "$dir/server/server-cert.pem" -days 365 -CAcreateserial -CAserial "$dir/ca/ca.srl"

openssl req -new -newkey rsa:2048 -nodes -subj "/CN=$client_name/" -keyout "$dir/clients/$client_name-privkey.pem" | openssl x509 -req -sha256 -CA "$dir/ca/ca-cert.pem" -CAkey "$dir/ca/ca-privkey.pem" -out "$dir/clients/$client_name-cert.pem" -days 365 -CAcreateserial -CAserial "$dir/ca/ca.srl"

openssl pkcs12 -export -in "$dir/clients/$client_name-cert.pem" -inkey "$dir/clients/$client_name-privkey.pem" -certfile "$dir/ca/ca-cert.pem" -password pass:123456 -name pykmip_client -out "$dir/clients/$client_name.p12"

echo "$client_name,users" > user_group_mapping.csv