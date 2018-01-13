#!/usr/bin/bash

./get.py | gawk '{ print strftime("[%Y-%m-%d %H:%M:%S]"), $0 }' >> getlog 2>&1
./table.py | gawk '{ print strftime("[%Y-%m-%d %H:%M:%S]"), $0 }' >> tbllog 2>&1
rsync -ruv --delete html /usr/share/nginx | gawk '{ print strftime("[%Y-%m-%d %H:%M:%S]"), $0 }' >> rsynclog 2>&1
