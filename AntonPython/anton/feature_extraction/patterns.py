'''
Created on May 16, 2016

@author: peter
'''
from collections import Counter
from collections import defaultdict
import gzip
from multiprocessing import Pool
import re
import time
import operator

import numpy

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton.feature_extraction import base
from anton.util import util


WEBT1_PATTERN_COUNT_FILE = "webt1_pattern_count.txt"

class PosPatternsExtractor(base.FeatureExtractor):

    def title(self):
        return "POS-Patterns"
    
    def feature_col_headers(self):
        return self.col_headers()
    
    def col_headers(self):
        return ["bestPattern" + str(i) for i in range(1, 1000)]

    def init(self, pos_to_df):
        return

    def extract_features_pos(self, pos_to_df):
        "This is just a dummy extractor. Pattern features have to be extracted with the Spark project."
        return
        
    def finish(self, df):
        return
    
class GoogleNGramPatternExtractor(base.FeatureExtractor):
    
    def __init__(self):       

        self.num_sentences = 95119665584

        self.web1t_dir = config.path_to_res("corpus_dir_web1t")

        self.pattern_length_to_start_ngram_to_gm_filename = defaultdict(dict)
        self.pattern_length_to_gm_filenames = defaultdict(list)
        
        ngram_dir = self.web1t_dir + "en/gz/"
        for pattern_length in range(3, 6):
            index_filename = ngram_dir + str(pattern_length) + "gms/" + str(pattern_length) + "gm.idx"
            for line in open(index_filename):
                parts = line.split("\t")
                gm_filename = parts[0]
                start_ngram = parts[1].rstrip()
                self.pattern_length_to_gm_filenames[pattern_length].append(gm_filename)
                self.pattern_length_to_start_ngram_to_gm_filename[pattern_length][start_ngram] = gm_filename
        
        self.pattern_to_count = Counter()
        self.pattern_length_to_patterns = {}
        for pattern_length in range(3, 6):
            self.pattern_length_to_patterns[pattern_length] = []
        self.pattern_to_line_index = Counter()
        self.pattern_to_instance_distance = Counter()
        i = 1
        for line in open(config.ws_path + "/AntonSpk/" + WEBT1_PATTERN_COUNT_FILE):
            parts = line.split('\t')
            pattern = parts[0]
            count = int(parts[1])
            pattern_length = len(pattern.split())
            self.pattern_length_to_patterns[pattern_length].append(pattern)
            self.pattern_to_count[pattern] = count
            self.pattern_to_line_index[pattern] = i
            
            tokens = pattern.split()
            wildcard_index_1 = tokens.index("(\w+)")
            self.pattern_to_instance_distance[pattern] = tokens[wildcard_index_1 + 1:].index("(\w+)") + 2
            
            i += 1
        
        
    def title(self):
        return "Google n-gram patterns"
    
    def feature_col_headers(self):
        return ["web1t_pattern_" + str(line_index) + "_lmi" for _, line_index in self.pattern_to_line_index.items()]
    
    def col_headers(self):
        instance_count_col_headers = ["web1t_instance_" + str(pattern_length) + "_gram_freq" for pattern_length, _ in self.pattern_length_to_patterns.items()]
        cooc_col_headers = ["web1t_pattern_" + str(line_index) + "_freq" for _, line_index in self.pattern_to_line_index.items()]
        return self.feature_col_headers() + instance_count_col_headers + cooc_col_headers

    def init(self, pos_to_df):
        return
        
    def extract_features_pos(self, pos_to_df):

        pattern_to_instance_to_count = defaultdict(Counter)

        for pattern_length, patterns in self.pattern_length_to_patterns.items():
            
            pattern_to_instance_to_ngrams, ngrams = self.prepare_ngrams(pattern_length, patterns, pos_to_df)

            ngram_to_count, instance_to_count = self.determine_ngram_and_instance_counts(pattern_length, ngrams, pos_to_df)

            for pattern in patterns:

                for pos in util.POS:
                    df = pos_to_df[pos]
                    
                    for instance, _ in df.iterrows():
                        pattern_instance_ngrams = pattern_to_instance_to_ngrams[pattern][instance]
                        count = ngram_to_count[pattern_instance_ngrams[0]] + ngram_to_count[pattern_instance_ngrams[1]]
                        pattern_to_instance_to_count[pattern][instance] = count
            
            for pos in util.POS:
                df = pos_to_df[pos]
                df["web1t_instance_" + str(pattern_length) + "_gram_freq"] = df.index.map(lambda instance: instance_to_count[instance])

        for pos in util.POS:
            df = pos_to_df[pos]
            
            for pattern_length, patterns in self.pattern_length_to_patterns.items():

                for pattern in patterns:
                    
                    pattern_line_index = self.pattern_to_line_index[pattern]
                    
                    cooc_col_header = "web1t_pattern_" + str(pattern_line_index) + "_freq"
                    df[cooc_col_header] = df.index.map(lambda instance: pattern_to_instance_to_count[pattern][instance])

                    numerator = self.num_sentences * df[cooc_col_header]
                    denominator = df["web1t_instance_" + str(self.pattern_to_instance_distance[pattern]) + "_gram_freq"] * self.pattern_to_count[pattern]
                    
                    pattern_lmi_col_header = "web1t_pattern_" + str(pattern_line_index) + "_lmi"
                    df[pattern_lmi_col_header] = df[cooc_col_header] * numpy.log(numerator / denominator)
                    df[pattern_lmi_col_header].replace(to_replace=numpy.inf, value=0, inplace=True)
                    df[pattern_lmi_col_header].fillna(value=-sys.maxsize, inplace=True)
        return
    
    def prepare_ngrams(self, pattern_length, patterns, pos_to_df):
        
        pattern_to_instance_to_ngrams = defaultdict(lambda: defaultdict(list))
        ngrams = []
        
        for pattern in patterns:
                
            for pos in util.POS:
                df = pos_to_df[pos]
                    
                for instance, _ in df.iterrows():
                        
                    parts = instance.split()
                    word_1, word_2 = parts[0], parts[1]
                    ngram_w1_w2 = pattern.replace("(\w+)", word_1, 1).replace("(\w+)", word_2, 1)
                    ngram_w2_w1 = pattern.replace("(\w+)", word_2, 1).replace("(\w+)", word_2, 1)
                    pattern_instance_ngrams = [ngram_w1_w2, ngram_w2_w1]
                    ngrams.extend(pattern_instance_ngrams)
                    pattern_to_instance_to_ngrams[pattern][instance].extend(pattern_instance_ngrams)
                        
        ngrams.sort()
        
        return pattern_to_instance_to_ngrams, ngrams
    
    def map_gm_files_to_ngrams(self, pattern_length, ngrams):
    
        start_ngrams = sorted([start_ngram for start_ngram, _ in self.pattern_length_to_start_ngram_to_gm_filename[pattern_length].items()])
        
        num_gm_files = len(start_ngrams)
         
        file_to_ngrams = defaultdict(list)
        i = j = 0
        while i < num_gm_files - 1:

            start_ngram = start_ngrams[i]
            next_start_ngram = start_ngrams[i + 1]

            while j < len(ngrams) and ngrams[j] < next_start_ngram:

                if ngrams[j] >= start_ngram:
                    gm_filename = self.pattern_length_to_start_ngram_to_gm_filename[pattern_length][start_ngram]
                    file_to_ngrams[gm_filename].append(ngrams[j])
                j += 1
                
            i += 1
            
        last_gm_filename = self.pattern_length_to_start_ngram_to_gm_filename[pattern_length][start_ngrams[num_gm_files - 1]]                    
        file_to_ngrams[last_gm_filename].extend(ngrams[i:]) 
    
        return file_to_ngrams
     
    def determine_ngram_and_instance_counts(self, pattern_length, ngrams, pos_to_df):

        pair_to_count = Counter()
        ngram_to_count = Counter()
        instance_to_count = Counter()
        
        pairs = set()
        for pos in util.POS:
            df = pos_to_df[pos]
            for instance, _ in df.iterrows():
                parts = instance.split()
                pairs.add(util.order_pair((parts[0], parts[1])))
        
        file_to_ngrams = self.map_gm_files_to_ngrams(pattern_length, ngrams)

        ngram_dir = self.web1t_dir + "en/gz/" + str(pattern_length) + "gms/"
        
        filenames = self.pattern_length_to_gm_filenames[pattern_length]
        num_files = len(filenames)
        for i in range(0, num_files, 4):
            
            pool = Pool()
            
            result1 = pool.apply_async(determine_ngram_and_pair_counts_in_file, [filenames[i], ngram_dir, pairs, file_to_ngrams[filenames[i]]])
            if not i + 1 > num_files - 1:
                result2 = pool.apply_async(determine_ngram_and_pair_counts_in_file, [filenames[i + 1], ngram_dir, pairs, file_to_ngrams[filenames[i + 1]]])    
            if not i + 2 > num_files - 1:
                result3 = pool.apply_async(determine_ngram_and_pair_counts_in_file, [filenames[i + 2], ngram_dir, pairs, file_to_ngrams[filenames[i + 2]]])    
            if not i + 3 > num_files - 1:
                result4 = pool.apply_async(determine_ngram_and_pair_counts_in_file, [filenames[i + 3], ngram_dir, pairs, file_to_ngrams[filenames[i + 3]]])    
            
            answer1 = result1.get(timeout=10000) 
            if not i + 1 > num_files - 1:  
                answer2 = result2.get(timeout=10000)
                answer1 = tuple(map(operator.add, answer2, answer1))
            if not i + 2 > num_files - 1: 
                answer3 = result3.get(timeout=10000)
                answer1 = tuple(map(operator.add, answer3, answer1))
            if not i + 3 > num_files - 1:  
                answer4 = result4.get(timeout=10000)
                answer1 = tuple(map(operator.add, answer4, answer1))
            
            pool.close()
            
            ngram_to_count += answer1[0]
            pair_to_count += answer1[1]

        for pair, count in pair_to_count.items():
            instance_to_count[pair[0] + " " + pair[1]] = count 
               
        return ngram_to_count, instance_to_count
        
    def finish(self, df):
        return

def determine_ngram_and_pair_counts_in_file(filename, ngram_dir, pairs, ngrams):
    
    ngram_to_count = Counter()
    pair_to_count = Counter()
    for pair in pairs:
        pair_to_count[pair] = 0
    
    i = 0
    num_ngrams = len(ngrams)
    
    start_time = time.time() 
    print("Processing " + filename)
    
    with gzip.open(ngram_dir + filename, 'r') as file:  
                        
        for line in file:
            parts = line.decode().split('\t')
            ngram = parts[0]
                
            tokens = ngram.split()
            try:
                pair = util.order_pair((tokens[0], tokens[-1]))
                
                if pair in pair_to_count:
                    pair_to_count[pair] += int(parts[1])
            except IndexError:
                pass
                    
            if ngrams and i < num_ngrams:
                if ngram == ngrams[i]:
                    ngram_to_count[ngram] = int(parts[1])
                    i += 1
                elif ngram > ngrams[i]:
                    i += 1
    
    print("Took" + str(time.time() - start_time) + " to process one file.") 
    
    return ngram_to_count, pair_to_count

def count_patterns_in_file(filename, ngram_dir, patterns, pattern_to_tokens, pattern_to_regex):
            
        pattern_to_count = Counter()
            
        print("Processing: " + filename) 
            
        start_time = time.time()   
        with gzip.open(ngram_dir + '/' + filename, 'r') as file:                 
            for line in file:
                
                parts = line.decode().split('\t')
                ngram = parts[0]
                
                ngram_tokens = set(ngram.split())
                
                for pattern in patterns:
                    if pattern_to_tokens[pattern].issubset(ngram_tokens):
                        if pattern_to_regex[pattern].match(ngram):
                            pattern_to_count[pattern] += int(parts[1])

        print("Took" + str(time.time() - start_time) + " to process one file.")
            
        return pattern_to_count
         
def prepare_web1t_patterns():
    
    web1t_dir = config.path_to_res("corpus_dir_web1t")
    
    ws_path = config.ws_path
    
    pattern_ranking_lines = []
    for pos in util.POS:
        lines = open(ws_path + "/AntonSpk/" + pos.tag + "_pattern_ranking.txt").readlines()
        pattern_ranking_lines.extend(lines)

    length_to_pattern_to_count = {}
    for pattern_length in range(2, 6):
        length_to_pattern_to_count[pattern_length] = Counter()

    pattern_to_regex = {}
    pattern_to_tokens = {}
    
    for line in pattern_ranking_lines:
        parts = line.split("\t")
        raw_pattern = parts[0]
        pattern = re.sub(r"/[^ ]*", "", raw_pattern)
        
        pattern_length = len(pattern.split())
        if pattern_length > 5:
            continue
        
        length_to_pattern_to_count[pattern_length][pattern] = 0
        pattern_to_regex[pattern] = re.compile(pattern)
        tokens = set(pattern.split())
        tokens.remove("(\w+)")
        pattern_to_tokens[pattern] = tokens
        
    for pattern_length, pattern_to_count in length_to_pattern_to_count.items():  
                            
        ngram_dir = web1t_dir + "en/gz/" + str(pattern_length) + "gms/"   

        filenames = [filename for filename in os.listdir(ngram_dir) if filename.endswith("gz")]

        patterns = [pattern for pattern in pattern_to_count.keys()]
        
        num_files = len(filenames) 
        for i in range(0, num_files, 4):
            
            pool = Pool()
            
            result1 = pool.apply_async(count_patterns_in_file, [filenames[i], ngram_dir, patterns, pattern_to_tokens, pattern_to_regex])
            if not i + 1 > num_files - 1:
                result2 = pool.apply_async(count_patterns_in_file, [filenames[i + 1], ngram_dir, patterns, pattern_to_tokens, pattern_to_regex])    
            if not i + 2 > num_files - 1:
                result3 = pool.apply_async(count_patterns_in_file, [filenames[i + 2], ngram_dir, patterns, pattern_to_tokens, pattern_to_regex])    
            if not i + 3 > num_files - 1:
                result4 = pool.apply_async(count_patterns_in_file, [filenames[i + 3], ngram_dir, patterns, pattern_to_tokens, pattern_to_regex])    
            
            answer1 = result1.get(timeout=10000) 
            if not i + 1 > num_files - 1:  
                answer2 = result2.get(timeout=10000)
                answer1 = answer2 + answer1
            if not i + 2 > num_files - 1: 
                answer3 = result3.get(timeout=10000)
                answer1 = answer3 + answer1
            if not i + 3 > num_files - 1:  
                answer4 = result4.get(timeout=10000)
                answer1 = answer4 + answer1
            
            pool.close()
                   
            pattern_to_count += answer1
                
    with open(config.ws_path + "/AntonSpk/" + WEBT1_PATTERN_COUNT_FILE, 'w') as webt1_file:
        
        for _, pattern_to_count in length_to_pattern_to_count.items(): 
            for pattern, count in pattern_to_count.items():
                
                webt1_file.write(pattern + '\t' + str(count) + '\n')                    

if __name__ == "__main__":
    
    prepare_web1t_patterns()
    