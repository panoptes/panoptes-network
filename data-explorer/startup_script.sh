#!/bin/sh

echo "Starting nginx"
sudo nginx -c nginx.conf

echo "Starting flask and bokeh"
flask run -h 127.0.0.1 -p 5000
