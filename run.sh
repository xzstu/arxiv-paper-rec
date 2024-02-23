yesterday=$(date -v-1d +%Y-%m-%d)

echo "dowloading data"
python down_data.py --date $yesterday

echo "runing rec"
python main.py --date $yesterday
