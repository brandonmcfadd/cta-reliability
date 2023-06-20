git pull
pip install -r requirements.txt
sudo systemctl restart api-service.service
sudo systemctl restart cta-reliability.service
sudo systemctl restart headways.service
sudo systemctl restart metra-reliability.service