from data_layer.paper_data import fetch_papers
import os
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str)
    args = parser.parse_args()
    save_path = os.path.join('./database/', args.date + "_papers.csv")
    print(f'- fetch paper in date {args.date}')
    fetch_papers(save_path, args.date)
