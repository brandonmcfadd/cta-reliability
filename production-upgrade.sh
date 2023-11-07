#!/bin/sh
cd $(dirname $0)
python3 -m pip install --upgrade pip
sudo git stash
sudo git stash drop
sudo git pull
sudo chown -R brandon_brandonmcfadden_com:brandon_brandonmcfadden_com .
sudo chmod +x production-upgrade.sh
pip install -r /home/brandon_brandonmcfadden_com/cta-reliability/requirements.txt
sudo systemctl restart cta-reliability.service
sudo systemctl restart headways.service
sudo systemctl restart metra-reliability.service
sudo systemctl restart api-service.service