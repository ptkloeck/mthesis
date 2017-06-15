'''
Created on Apr 10, 2016

@author: peter
'''
from gensim.models.word2vec import Word2Vec
from anton import config

model = Word2Vec.load_word2vec_format(config.ws_path + "/../Word2Vec/GoogleNews-vectors-negative300.bin", binary=True)

print(model.similarity("woman", "man"))
