import yaml
import os
from pathlib import PosixPath
from model import recommend
import pandas as pd
from emails import send_email
from typing import List
import argparse

DB_PATH = './database'


def _read_user_profile(path):
    print(f'- read user profile from {path}')
    with open(path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)
    

def read_user_profiles(dir_path: str):
    paths = list(PosixPath(dir_path).glob('*.yaml'))
    user_cfgs = []
    for path in paths:
        if str(path).find('example.yaml') == -1:
            user_cfgs.append(_read_user_profile(path))
    return user_cfgs


def get_candidates_df(date: str):
    csv_path = os.path.join(DB_PATH, f"{date}_papers.csv")
    print(f'- read candidates data from {csv_path}')
    return pd.read_csv(csv_path)


def to_html(df: pd.DataFrame, idxs: List[int], date: str):
    sub_df = df.iloc[idxs, :][['title', 'entry_id']]
    html_output = '<html><body>'
    html_output += f"<h2>{date} Papers Rec</h2>"
    html_output += "<ul>"

    for idx, row in sub_df.iterrows():
        html_output += f'<li> {row[0]} [<a href="{row[1]}">get</a>]</li>'
    html_output += '</ul></body></html>'
    return html_output


def run(date: str):
    user_cfgs = read_user_profiles('./configs/users_profile')
    df = get_candidates_df(date)
    topk = 10
    result = {}
    for cfg in user_cfgs:
        idxs = recommend(','.join(cfg['interests']), df['abstract'].tolist(), topk)
        print('- send emails.')
        send_email(
            to_html(df, idxs, date), 
            "Daily Paper Rec", 
            'AndrewGuan <884691896@qq.com>',
            f"{cfg['username']} <{cfg['user_emails']}>", 
            cfg['user_emails']
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str)
    args = parser.parse_args()
    
    run(args.date)
