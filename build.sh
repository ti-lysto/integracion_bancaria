#!/bin/bash
echo "=== Moving files to wwwroot ==="
cp -r . /home/site/wwwroot/
cd /home/site/wwwroot
echo "=== Files in wwwroot ==="
ls -la
