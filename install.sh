#!/bin/bash

set -e
set -x

# gcc libffi-dev
sudo apt-get install python3-pip virtualenv screen unzip -y

if [ -z "$VIRTUAL_ENV" ]; then
    virtualenv -p python3 D4GENV
    echo export D4G_HOME=$(pwd) >> ./D4GENV/bin/activate
    . ./D4GENV/bin/activate
fi
python3 -m pip install -r requirement.txt

# pushd web/
# ./update_web.sh
# popd


python3 -m pip install -r requirement.txt

git clone https://github.com/D4-project/d4-core.git
git clone https://github.com/D4-project/d4-goclient.git

pushd d4-goclient
gox -output="../exe_goclient/d4-goclient_{{.OS}}_{{.Arch}}"
sleep 5
find . -type f -exec sha256sum {} \; > ../sha256sum.txt
popd

# REDIS #
test ! -d redis/ && git clone https://github.com/antirez/redis.git
pushd redis/
git checkout 5.0
make
popd
