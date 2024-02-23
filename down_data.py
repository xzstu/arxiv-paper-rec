from data_layer.paper_data import yesterday_papers, yesterday_date
import os
from datetime import datetime, timedelta


if __name__ == '__main__':
    given_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    save_path = os.path.join('./database/', yesterday_date(given_date) + "_papers.csv")
    yesterday_papers(save_path, given_date)

