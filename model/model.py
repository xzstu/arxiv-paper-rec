from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from typing import List
import numpy as np


#Mean Pooling - Take attention mask into account for correct averaging
def _mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def _encoding(sentence, model, tokenizer):
    # Tokenize sentences
    if isinstance(sentence, str):
        sentence = [sentence]
    encoded_input = tokenizer(sentence, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = _mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    return F.normalize(sentence_embeddings, p=2, dim=1)


def recommend(sentence1: str, candidates: List[str], topk: int) -> List[int]:
    # Load model from HuggingFace Hub
    print('- load tokenizer')
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2', cache_dir='./hugs')
    print('- load model')
    model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2', cache_dir='./hugs')
    print('- encoding')
    query_emb = _encoding(sentence1, model, tokenizer)
    candidates_emb = _encoding(candidates, model, tokenizer)

    print('- sorting')
    sim = query_emb @ candidates_emb.T
    idxs = sim.argsort(descending=True)[0].tolist()[:topk]
    return idxs

