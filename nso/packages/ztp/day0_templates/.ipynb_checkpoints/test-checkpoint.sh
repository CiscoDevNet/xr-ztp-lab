#!/bin/sh

hostname ${HOSTNAME}

curl -X POST http://198.18.134.50:8181/ztp/status/${SERIAL}/1