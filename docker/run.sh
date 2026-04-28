#!/bin/bash

cd /etc/pykmip

noslugs=false
if [ "$1" == "--noslugs" ]; then
    noslugs=true
fi

log_dir="/data/log"
if $noslugs; then
  sed -r -i "s/^enabled = True/enabled = False/" server.conf
fi
for definition in $(env | grep '^PYKMIP_'); do
  key="${definition%%=*}"
  key="${key:7}"
  key="${key,,}"
  value="${definition#*=}"
  if [ "$key" == "log_dir" ]; then
    log_dir="${value%/}"
    continue
  fi

  if grep -E -q "^$key[[:space:]=]" server.conf; then
    sed -r -i "s#^$key[[:space:]=].*#$key = $value#" server.conf
  else
    echo "$key = $value" >> server.conf
  fi
done

if [ "$log_dir" != "/data/log" ]; then
  sed -r -i "s#/data/log#$log_dir#g" slugs.conf
else
  mkdir /data/log 2>/dev/null
fi

if ! compgen -e | grep -q -i 'PKMIP_DATABASE_PATH'; then
  mkdir /data/db 2>/dev/null
fi

if [ -v SLUGS_USER_GROUP_MAPPING ]; then
  sed -r -i "s#^user_group_mapping.*#user_group_mapping = '$SLUGS_USER_GROUP_MAPPING'#" slugs.conf
fi

cd /

# Install CA certificate
cp -L "/data/server/ca-cert.pem" "/usr/local/share/ca-certificates/ca-cert.crt"
update-ca-certificates

# Start the Slugs server
if ! $noslugs; then
  slugs -c /etc/pykmip/slugs.conf & sleep 1
fi

# Start the PyKMIP server
pykmip-server --config_path=/etc/pykmip/server.conf --log_path="$log_dir/pykmip.log" 2>&1