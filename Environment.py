import torch
import random
from transformers import BertTokenizer, BertModel
from copy import copy
from config import *
from util import *
from Agent import Agent

class Environment():
    def __init__(self, bert_model, bert_tokenizer):
        self.bert_model = bert_model
        self.tokenizer = bert_tokenizer
        self.vocab_size = self.tokenizer.vocab_size
        self.observation_space = STATE_SIZE
    
    def reset(self):
        '''
        IN:
        nothing
        OUT:
        obs: [STATE_SIZE,](torch.FloatTensor)
        '''
        self.sentence = []
        obs = self.encode(self.sentence)
        return obs

    def step(self, action):
        '''
        IN:
        action: single integer
        OUT:
        tuple (obs, 0, done, None) where
            obs: [STATE_SIZE,](torch.FloatTensor)
            done: single boolean value
        '''
        self.sentence.append(action)
        if len(self.sentence) >= GEN_MAX_LEN or action == SEP_TOKEN_IDX:
            done = True
            if action == SEP_TOKEN_IDX:
                self.sentence.pop(-1)
        else:
            done = False
        obs = self.encode(self.sentence)
        return obs, 0, done, None

    def encode(self, sentence):
        tmp = copy(sentence)
        tmp.append(SEP_TOKEN_IDX)
        tmp.insert(0, CLS_TOKEN_IDX)
        tmp = torch.LongTensor(tmp).view(1, -1).to(DEVICE)
        with torch.no_grad():
            obs = self.bert_model(tmp)[0][0][0]
        return obs

    def id_to_string(self):
        tokens = []
        for index in self.sentence:
            token = self.tokenizer._convert_id_to_token(index)
            tokens.append(token)
        return self.tokenizer.convert_tokens_to_string(tokens)




if __name__ == '__main__':
    bert_model, bert_tokenizer = get_bert_model_and_tokenizer()
    env = Environment(bert_model, bert_tokenizer)
    agent = Agent(bert_model)
    dist = torch.distributions.Categorical(probs=torch.full((2,), fill_value=0.5))
    for _ in range(10):
        s = env.reset()
        c = dist.sample().numpy().item()
        d = False
        while not d:
            a, log_prob = agent.get_action(s, c)
            next_s, r, d, _ = env.step(a)
            agent.store(s, a, c, d, next_s, log_prob)
            s = next_s
        print(env.sentence)
        print(env.id_to_string())
    agent.long_memory.check_update()