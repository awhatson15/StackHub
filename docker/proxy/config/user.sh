#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

echo "Start to change nginxproxymanage users"
username="help@websoft9.com"
password=$(openssl rand -base64 16 | tr -d '/+' | cut -c1-16)
token=""
while [ -z "$token" ]; do
    sleep 5
    login_data=$(curl -X POST -H "Content-Type: application/json" -d '{"identity":"admin@example.com","scope":"user", "secret":"changeme"}' http://login_data=$(curl -X POST -H "Content-Type: application/json" -d '{"identity":"admin@example.com","scope":"user", "secret":"changeme"}' http://localhost:81/api/tokens)
    token=$(echo $login_data | jq -r '.token')
done

echo "Change username(email)"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{"email": "'$username'", "nickname": "admin", "is_disabled": false, "roles": ["admin"]}'  http://localhost:81/api/users/1

echo "Update password"
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{"type":"password","current":"changeme","secret":"'$password'"}'  http://localhost:81/api/users/1/auth