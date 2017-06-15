'''
Created on 07.02.2016

@author: Peter
'''
import unittest
import time

from anton.util import jobim_reader
from anton import config

class TestJoBimReader(unittest.TestCase):
    
    def test_readlines(self):
        
        start_time = time.time()
        
        num_lines = 0
        for _ in jobim_reader.readlines(config.path_to_res("corpus_dir"), True):
            num_lines += 1
            
            if num_lines > 1000000:
                break
        
        print(time.time() - start_time)
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'TestPatternCount.testName']
    unittest.main()