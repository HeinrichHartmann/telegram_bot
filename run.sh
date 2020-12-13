#!/bin/bash

TOKEN="$(cat token.txt)"

docker run -v ~/Stack:/work/dl -e TOKEN=$TOKEN -it --rm docker.heinrichhartmann.net:5000/telegram_bot:latest bash -c '
while true
do
  printf "pull %s\n" $(date +"%FT%T%Z")
  telegram_bot pull $TOKEN
  sleep 300
done
'
