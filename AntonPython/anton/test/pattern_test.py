'''
Created on 20.11.2015

@author: Peter
'''
import unittest

import anton.feature_extraction.lin_count as lc
from anton.feature_extraction.lin_count import PatternCount
from anton.feature_extraction.lin_count import either_or_pattern
from anton.feature_extraction.lin_count import from_to_pattern


class TestPatternCount(unittest.TestCase):

    def setUp(self):
        
        self.good_bad_instance = ("good", "bad")
        self.active_passive_instance = ("passive", "active") 
             
        self.sentence_1 = "Either good or bad."       
        self.sentence_2 = "This is either good or bad."        
        self.sentence_3 = "Is this either passive or active?"        
        self.sentence_4 = "Was ist da denn los?"       
        self.sentence_5 = "Either good or good."       
        self.sentence_6 = "This is either bad or bad."
        self.sentence_7 = "He went from good to bad."
        
    def test_check_sentence(self):

        relations = either_or_pattern.check_sentence(self.sentence_1)
        self.assertEqual(relations[0], self.good_bad_instance)
        
        relations = either_or_pattern.check_sentence(self.sentence_2)
        self.assertEqual(relations[0], self.good_bad_instance)
        
        relations = either_or_pattern.check_sentence(self.sentence_3)
        self.assertEqual(relations[0], self.active_passive_instance)
        
        relations = either_or_pattern.check_sentence(self.sentence_4)
        self.assertTrue(len(relations) == 0)
        
        relations = either_or_pattern.check_sentence(self.sentence_5)
        self.assertEqual(relations[0], ("good", "good"))
        
        relations = either_or_pattern.check_sentence(self.sentence_6)
        self.assertTrue(relations[0], ("bad", "bad"))
        
        relations = from_to_pattern.check_sentence(self.sentence_7)
        self.assertEqual(relations[0], self.good_bad_instance)
        
    def test_pattern_count(self):
        
        lin_count = PatternCount.from_files("../res/word_pattern_count.tsv", "../res/instance_pattern_count.tsv")

        self.assertEqual(231, lin_count.get_word_2_count("democracy", lc.FROM_TO_PATTERN_ID))
        self.assertEqual(95, lin_count.get_instance_count(("democracy", "dictatorship"), lc.FROM_TO_PATTERN_ID))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'TestPatternCount.testName']
    unittest.main()
