'''
Created on 05.01.2016

@author: Peter
'''
import gzip
import io
import os, tempfile
import subprocess
import time
from enum import Enum
import re

from anton.util import util

class JB_POS(Enum):
    ADJ = (["jj"])
    """
    NN    Noun, singular or mass
    NNS    Noun, plural
    NNP    Proper noun, singular
    NNPS    Proper noun, plural 
    """
    NOUN = (["nn", "nns" "nnp", "nnps"])
    VERB = (["vb"])
    
    def __init__(self, tags):
        self.tags = tags
        
    @property
    def pattern(self):
        regex = "/(" + self.tags[0]
        for tag in self.tags[1:]:
            regex += '|' + tag
        regex += ')'
        return re.compile(regex)

def jb_pos(pos):
    return {util.POS.ADJ : JB_POS.ADJ,
            util.POS.NOUN: JB_POS.NOUN,
            util.POS.VERB: JB_POS.VERB}[pos]

def extract_tokens_with_pos(tagged_sen, pos):
    
    pos = jb_pos(pos)
    
    tokens = []
    
    for token_pos in tagged_sen.split():
        
        parts = token_pos.split('/') 
        if len(parts) < 2:
            continue
        token, pos_tag = parts[0], parts[1]
        
        if pos_tag in pos.tags:
            tokens.append(token)

    return tokens

def extract_tokens(tagged_sen):
    
    tokens = []
    
    for token_pos in tagged_sen.split():
        
        parts = token_pos.split('/') 
        tokens.append(parts[0])

    return tokens
    
def readlines(corpus_dir, on_linux):
    
    parts_processed_counter = 0
    start_time = time.time()
    
    for filename in os.listdir(corpus_dir):

        if filename.startswith('part'):

            if on_linux:

                tmpdir = tempfile.mkdtemp()
                tmpfilename = os.path.join(tmpdir, 'myfifo')
                try:
                    os.mkfifo(tmpfilename)
                except OSError as e:
                    print("Failed to create FIFO: %s", e)
                    break
                
                p = subprocess.Popen("gzip --stdout -d " + corpus_dir + "/" + filename + " > %s" % tmpfilename, shell=True)
                f = io.open(tmpfilename, "r")
 
                while True:
                    line = f.readline()
                    if not line: break
                    yield line
 
                f.close()
                p.wait()
 
                os.remove(tmpfilename)
                os.rmdir(tmpdir)
                
            else:
                with gzip.open(corpus_dir + '/' + filename) as file:

                    for line in file:           
                        yield line.decode()
            
            parts_processed_counter += 1
            if parts_processed_counter >= 500:
                print("Took" + str(time.time() - start_time) + "Processed another 500 parts")
                start_time = time.time()
                parts_processed_counter = 0 
            