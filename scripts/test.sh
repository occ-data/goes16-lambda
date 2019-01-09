#!/bin/bash
/opt/python/cp27-cp27mu/bin/pip install -r /app/requirements.txt

cd /app/
mkdir -p /tmp
cp /app/test/OR_ABI-L2-MCMIPF-M3_G16_s20183131815356_e20183131826123_c20183131826218.nc /tmp/tmp.nc
/opt/python/cp27-cp27mu/bin/python src/handler.py
