git stash
git stash drop
git pull
pip-upgrade --skip-virtualenv-check /home/brandon_brandonmcfadden_com/cta-reliability/requirements.txt
sudo systemctl restart api-service.service
sudo systemctl restart cta-reliability.service
sudo systemctl restart headways.service
sudo systemctl restart metra-reliability.service