#!/bin/sh
pid=`ps -aux | grep -v 'grep' | grep 'uwsgi vmmanager.xml --plugin python' | awk  '{print $2}' | awk 'NR==1'`
if [ -z $pid ]; then
echo ' '
else
echo "kill $pid"
sudo kill $pid
fi
sudo uwsgi vmmanager.xml --plugin python
