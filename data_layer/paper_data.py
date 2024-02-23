import arxiv
import pandas as pd
from typing import Generator
from datetime import datetime, timedelta
import time


cats = [
    'cs.AI', 'cs.CL', 'cs.CV', 'cs.IR', 'cs.LG', 'cs.MA', 'cs.MM',
]


class DropDuplicates:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DropDuplicates, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, 'inited'):
            self.cur_has = set()
            self.inited = True
    
    def exist(self, it):
        if it in self.cur_has:
            return True
        else:
            self.cur_has.add(it)
            return False


def to_df(results: Generator, file_path, reqire_date = None) -> int:
    drop_handler = DropDuplicates()

    datas = {
        'publish_date': [],
        'entry_id': [], 
        'title': [], 
        'abstract': [], 
        'primary_category': [],
        'categories': []
    }

    for it in results:
        if drop_handler.exist(it.title):
            continue

        if reqire_date is None or it.published.strftime('%Y-%m-%d') == reqire_date:
            datas['publish_date'].append(it.published.strftime('%Y-%m-%d'))
            datas['entry_id'].append(it.entry_id)
            datas['title'].append(it.title)
            datas['abstract'].append(it.summary)
            datas['primary_category'].append(it.primary_category)
            datas['categories'].append(it.categories)
    
    return pd.DataFrame(datas)


def today_date() -> str:
   return datetime.now().strftime('%Y-%m-%d')


def format_cat_query(cats):
    res = []
    for it in cats:
        res.append(f'cat:{it}')
    return '+OR+'.join(res)


def yesterday_date(given_date: str = None):
    if given_date is not None:
        return given_date
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def fetch_papers(save_path, given_date: str = None):
    client = arxiv.Client()
    
    dfs = []
    paper_nums = 0
    for cat in cats:
        results = arxiv.Search(
            query=f'cat:{cat}',
            max_results=500,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        print(f' - fetching cat:{cat}...')
        results = client.results(results)
        print(f' - parse to dataframe...')
        dfs.append(to_df(results, save_path, yesterday_date(given_date)))
        paper_nums += dfs[-1].shape[0]
        time.sleep(3)
    
    print(f'- get {paper_nums} papers in {yesterday_date(given_date)}!')

    print(f'- saving to {save_path}...')
    all_df = pd.concat(dfs, axis=0)
    all_df = all_df.drop_duplicates(subset=['title'], ignore_index=True)
    all_df.to_csv(save_path, index=False)
    

