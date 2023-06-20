git stash
git stash drop
git pull
pip install -r requirements.txt
chmod +x production-upgrade.sh export_7_days_json_data.py export_7_days_arrivals.py export_1_month_arrivals.py main.py metra.py station_headways.py station-tracking.py
sudo systemctl restart api-service.service
sudo systemctl restart cta-reliability.service
sudo systemctl restart headways.service
sudo systemctl restart metra-reliability.service