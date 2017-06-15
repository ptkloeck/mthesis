'''
Created on Apr 27, 2016

@author: peter
'''
from collections import Counter
import os
import sys

import nltk
import pandas
from sklearn import cross_validation
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.grid_search import GridSearchCV

import numpy as np

from time import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from anton import config
from anton import feature_extraction
from anton import learn
from anton.util import util

def gre_to_classifier_tsv():
    
    wsj = nltk.corpus.brown.tagged_words(tagset="universal")
    cfd = nltk.ConditionalFreqDist(wsj)

    with open(config.path_to_res("gre_testset").replace(".tsv", ".txt"), 'r') as gre_raw:
        with open(config.path_to_res("gre_testset"), 'w') as gre_data:
            
            gre_data.write("\tpos_tag\n")

            written_instance_lines = []

            for line in gre_raw:

                target, choices, _ = devide_line(line)
              
                words = []
                words.append(target)
                words.extend(choices)
   
                pos = most_probable_pos_tag(words, cfd)
            
                for choice in choices:
                    pair = util.order_pair((target, choice))
                    index_key = util.ordered_pair_to_index_key(pair)
                    
                    instance_line = index_key + '\t' + pos + '\n'
                    if not instance_line in written_instance_lines:
                        written_instance_lines.append(instance_line)
                        gre_data.write(instance_line)

def devide_line(gre_line):
    
    gre_line = gre_line.rstrip('\n')
                
    parts = gre_line.split(':')

    target = parts[0]
    choices = parts[1].strip().split(' ')
    
    answer = parts[3].strip()
    
    return (target, choices, answer)
                    
def most_probable_pos_tag(words, cfd):

    tag_to_freq = Counter()
    for word in words:
        most_common_tags = cfd[word].most_common()
        if most_common_tags:
            most_common_tag = most_common_tags[0][0]
            if most_common_tag == "ADV":
                most_common_tag = "ADJ"
            tag_to_freq[most_common_tag] += 1
    
    most_probable_tag = "adj"
    max_freq = 0       
    for tag, freq in tag_to_freq.items():
        if freq > max_freq:
            max_freq = freq
            most_probable_tag = tag.lower()
    
    if most_probable_tag == "adp":
        most_probable_tag = "adj"   
        
    return most_probable_tag

def add_gold_prediction_gre():
    
    wsj = nltk.corpus.brown.tagged_words(tagset="universal")
    cfd = nltk.ConditionalFreqDist(wsj)
    
    gre_path = config.path_to_res("gre_testset")
    
    pos_tag_to_prediction_df = learn.read_prediction_dfs(gre_path)
    
    for _, prediction_df in pos_tag_to_prediction_df.items():
        prediction_df["rel_class"] = 2
    
    with open(config.path_to_res("gre_testset").replace(".tsv", ".txt"), 'r') as gre_raw:
        
        for line in gre_raw:

            target, choices, answer = devide_line(line)
            
            words = []
            words.append(target)
            words.extend(choices)
            
            pos = most_probable_pos_tag(words, cfd)
            print(pos)
            prediction_df = pos_tag_to_prediction_df[pos]
            
            prediction_df.set_value(util.pair_to_index_key((answer, target)), "rel_class", 1)
            
    for pos_tag, prediction_df in pos_tag_to_prediction_df.items():
        
        prediction_df.to_csv(gre_path.replace(".tsv", '_' + pos_tag + "_predicted.tsv"), sep='\t')
            
def accuracy_on_gre():
    
    wsj = nltk.corpus.brown.tagged_words(tagset="universal")
    cfd = nltk.ConditionalFreqDist(wsj)
    
    gre_path = config.path_to_res("gre_testset")
    # learn.extract_features_to_files(gre_path, [x for x in feature_extraction.FeatureCategory])
    
    # learn.classify_file(gre_path, False, [x for x in feature_extraction.FeatureCategory])
    
    pos_tag_to_prediction_df = learn.read_prediction_dfs(gre_path)

    num_lines = 0
    num_right = 0
    num_answered_clearly = 0
    num_right_clearly = 0
    with open(config.path_to_res("gre_testset").replace(".tsv", ".txt"), 'r') as gre_raw:
        
        for line in gre_raw:

            target, choices, answer = devide_line(line)
            
            words = []
            words.append(target)
            words.extend(choices)
   
            pos = most_probable_pos_tag(words, cfd)
            prediction_df = pos_tag_to_prediction_df[pos]
            
            print(target + " " + pos)
            
            max_ant_proba = 0
            chosen_ant = ""
            for choice in choices:
                index_key = util.pair_to_index_key((target, choice))
                
                if not index_key in prediction_df.index:
                    for pos in util.POS:
                        prediction_df = pos_tag_to_prediction_df[pos.tag]
                        if index_key in prediction_df.index:
                            break
                        
                ant_proba = prediction_df.loc[index_key, learn.PREDICT_PROBA_ANT_COL_HEADER]
                ant_proba = float(ant_proba)
                    
                print(" " + choice + " " + str(ant_proba) + ',')

                if ant_proba > max_ant_proba:
                    max_ant_proba = ant_proba
                    chosen_ant = choice
            
            print(answer + '\n')
            
            if max_ant_proba > 0.5 and pos != "verb":
                num_answered_clearly += 1
                
            if chosen_ant == answer:
                num_right += 1
                if max_ant_proba > 0.5 and pos != "verb":
                    num_right_clearly += 1
                    
            num_lines += 1
            
    print(float(num_right / num_lines))
    print(float(num_right_clearly / num_answered_clearly))
    print(num_answered_clearly)
    print(num_lines)

def eval_turn_lzqz(res_id, feature_categories):
    
    data_path = config.path_to_res(res_id)
    # learn.extract_features_to_files(data_path)
    #learn.classify_file(data_path, True, feature_categories)
    learn.compute_metrics(data_path)
            
def eval_turn(feature_categories):
    eval_turn_lzqz("turn_testset", feature_categories)
    
def eval_lqzq(feature_categories):
    eval_turn_lzqz("lzqz_testset", feature_categories)

def cross_val_turn():
    
    data_path = config.path_to_res("turn_testset")
    dfs = []
    for pos in util.POS:
        pos_data_path = data_path.replace(".tsv", "_" + pos.tag + ".tsv")
        df_pos = learn.read_dataframe(pos_data_path)
        dfs.append(df_pos)
    df = pandas.concat(dfs)
    print(len(df))
    
    feature_categories = [x for x in feature_extraction.FeatureCategory]
    feature_categories.remove(feature_extraction.FeatureCategory.PATTERNS)
     
    y = df["rel_class"] 
    X, _ = learn.feature_matrix(df, feature_categories)
    
    clf = RandomForestClassifier(n_estimators=100)

    scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring='f1_weighted', n_jobs=-1)
    print("Cross-validation for turn data set: " + str(scores.mean()))
               
def cross_val_wn(feature_categories):
    
    print("Crossvalidation for wn data sets for feature_categories: " + str(feature_categories))
    for pos in util.POS:
        cross_val_wn_data(pos, True, feature_categories)
        cross_val_wn_data(pos, False, feature_categories)
                
def cross_val_wn_data(pos, ant_syn, feature_categories):
    
    df = learn.load_wn_dataset(pos, ant_syn)

    y = df["rel_class"].values
    # antonyms:1 everything else (hyponyms etc.):2
    y[y > 1] = 2
    
    X, _ = learn.feature_matrix(df, feature_categories)
    
    clf = RandomForestClassifier(n_estimators=100)

    scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring='f1_weighted', n_jobs=-1)
    print("Cross-validation for pos:" + pos.tag + " and ant_syn:" + str(ant_syn) + ": " + str(scores.mean()))

def compare_classifiers_wn_data():
    
    feature_categories = [x for x in feature_extraction.FeatureCategory]
    
    names = ["Nearest Neighbors", "Linear SVM", "RBF SVM", "Decision Tree",
         "Random Forest", "Naive Bayes", "Logistic Regression"]
    classifiers = [
                   KNeighborsClassifier(3),
                    SVC(kernel="linear", C=0.025),
                    SVC(gamma=2, C=1),
                    DecisionTreeClassifier(),
                    RandomForestClassifier(n_estimators=100),
                    GaussianNB(),
                    LogisticRegression()]
    
    columns = ["f-score_adj", "f-score_noun", "f-score_verb"]   
    df_scores = pandas.DataFrame(index=names, columns=columns)
    
    for pos in util.POS:
        df = learn.load_wn_dataset(pos, False)
    
        X, _ = learn.feature_matrix(df, feature_categories)
        X = StandardScaler().fit_transform(X)
        y = df["rel_class"].values
        # antonyms:1 everything else (hyponyms etc.):2
        y[y > 1] = 2
    
        for i, clf in enumerate(classifiers):
            f1_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="f1_weighted", n_jobs=-1)
            f1 = "{:.4f}".format(f1_scores.mean())
            
            df_scores.loc[names[i], "f-score_" + pos.tag] = f1
    
    print(df_scores.to_latex(escape=False))

def fit_hyper_params_rf():
    
    feature_categories = [x for x in feature_extraction.FeatureCategory]
    
    df = learn.load_wn_dataset(util.POS.ADJ, True)
    
    X, _ = learn.feature_matrix(df, feature_categories)
    X = StandardScaler().fit_transform(X)
    y = df["rel_class"].values
    
    # Utility function to report best scores
    def report(grid_scores, n_top=3):
        top_scores = sorted(grid_scores, key=itemgetter(1), reverse=True)[:n_top]
        for i, score in enumerate(top_scores):
            print("Model with rank: {0}".format(i + 1))
            print("Mean validation score: {0:.3f} (std: {1:.3f})".format(
              score.mean_validation_score,
              np.std(score.cv_validation_scores)))
            print("Parameters: {0}".format(score.parameters))
            print("")
        
    # use a full grid over all parameters
    param_grid = {"max_depth": [3, None],
              "max_features": [1, 3, 10],
              "min_samples_split": [1, 3, 10],
              "min_samples_leaf": [1, 3, 10],
              "bootstrap": [True, False],
              "criterion": ["gini", "entropy"]}
    
    param_grid = {"n_estimators": [20, 60, 100, 140]}
    
    # clf = RandomForestClassifier(n_estimators=20)
    clf = RandomForestClassifier()
    
    # run grid search
    grid_search = GridSearchCV(clf, param_grid=param_grid)
    start = time()
    grid_search.fit(X, y)

    print("GridSearchCV took %.2f seconds for %d candidate parameter settings."
    % (time() - start, len(grid_search.grid_scores_)))
    report(grid_search.grid_scores_)
    
def ablation_test_wn_data(ant_syn):
    
    all_categories = [x for x in feature_extraction.FeatureCategory]
    
    index = [util.feature_category_to_latex(feature_category) for feature_category in feature_extraction.FeatureCategory]
    columns = ["precision_adj", "recall_adj", "f-score_adj", "precision_noun", "recall_noun", "f-score_noun", "precision_verb", "recall_verb", "f-score_verb"]   
    df_scores = pandas.DataFrame(index=index, columns=columns)
    
    for pos in util.POS:
        
        df = learn.load_wn_dataset(pos, ant_syn)

        y = df["rel_class"].values
        # antonyms:1 everything else (hyponyms etc.):2
        y[y > 1] = 2
    
        print ("All features are: " + str(all_categories))
    
        X, _ = learn.feature_matrix(df, all_categories)
    
        clf = RandomForestClassifier(n_estimators=100)

        f1_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="f1_weighted", n_jobs=-1)
        precision_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="precision", n_jobs=-1)
        recall_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="recall", n_jobs=-1)
        f1 = "{:.4f}".format(f1_scores.mean())
        precision = "{:.4f}".format(precision_scores.mean())
        recall = "{:.4f}".format(recall_scores.mean())
        
        row = "all"
        df_scores.loc[row, "precision_" + pos.tag] = precision
        df_scores.loc[row, "recall_" + pos.tag] = recall
        df_scores.loc[row, "f-score_" + pos.tag] = f1
            
        for i in range(len(all_categories)):
        
            removed_category = all_categories[i]
        
            feature_categories = list(all_categories)
            del(feature_categories[i])
        
            X, _ = learn.feature_matrix(df, feature_categories)
    
            clf = RandomForestClassifier(n_estimators=100)

            f1_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="f1_weighted", n_jobs=-1)
            precision_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="precision", n_jobs=-1)
            recall_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="recall", n_jobs=-1)
            f1 = "{:.4f}".format(f1_scores.mean())
            precision = "{:.4f}".format(precision_scores.mean())
            recall = "{:.4f}".format(recall_scores.mean())
            
            row = util.feature_category_to_latex(removed_category)
            df_scores.loc[row, "precision_" + pos.tag] = precision
            df_scores.loc[row, "recall_" + pos.tag] = recall
            df_scores.loc[row, "f-score_" + pos.tag] = f1
    
    print(df_scores.to_latex(escape=False))
        
def single_categorie_test_wn(ant_syn):
    
    index = [util.feature_category_to_latex(feature_category) for feature_category in feature_extraction.FeatureCategory]
    columns = ["precision_adj", "recall_adj", "f-score_adj", "precision_noun", "recall_noun", "f-score_noun", "precision_verb", "recall_verb", "f-score_verb"]   
    df_scores = pandas.DataFrame(index=index, columns=columns)
    
    for pos in util.POS:
        
        df = learn.load_wn_dataset(pos, ant_syn)
    
        y = df["rel_class"].values
        y[y > 1] = 2
    
        for feature_category in feature_extraction.FeatureCategory:
        
            X, _ = learn.feature_matrix(df, [feature_category])
    
            clf = RandomForestClassifier(n_estimators=100)
        
            f1_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="f1_weighted", n_jobs=-1)
            precision_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="precision", n_jobs=-1)
            recall_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring="recall", n_jobs=-1)
            f1 = "{:.4f}".format(f1_scores.mean())
            precision = "{:.4f}".format(precision_scores.mean())
            recall = "{:.4f}".format(recall_scores.mean())
            
            row = util.feature_category_to_latex(feature_category)
            df_scores.loc[row, "precision_" + pos.tag] = precision
            df_scores.loc[row, "recall_" + pos.tag] = recall
            df_scores.loc[row, "f-score_" + pos.tag] = f1

    print(df_scores.to_latex(escape=False))

def test_web1t_pruning():

    ns = [1, 5, 10, 50, 100, 200, 300, 400, 500]

    columns = ["f-score_adj", "f-score_noun", "f-score_verb"]   
    df_scores = pandas.DataFrame(index=ns, columns=columns)
    
    pattern_id_to_pattern = util.pattern_id_to_pattern(True)
    pattern_to_score = util.web1t_pattern_to_scores()
    
    pattern_id_scores = []
    for pattern_id, pattern in pattern_id_to_pattern.items():
        pattern_id_scores.append((pattern_id, pattern_to_score[pattern]))
    
    best_pattern_id_scores = sorted(pattern_id_scores, key=lambda tup: tup[1], reverse=True)    
    
    for pos in util.POS:
    
        df = learn.load_wn_dataset(pos, False)
    
        y = df["rel_class"].values
        y[y > 1] = 2
    
        for n in ns:
        
            best_pattern_ids = [pattern_id_score[0] for pattern_id_score in best_pattern_id_scores[:n]]
        
            df_best_patterns = df[best_pattern_ids]   
            learn.order_features(df_best_patterns)
        
            X = df_best_patterns.values
            X = StandardScaler().fit_transform(X)
    
            clf = RandomForestClassifier(n_estimators=100)
            # clf = LogisticRegression()
        
            f1_scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring='f1_weighted', n_jobs=-1)
            df_scores.loc[n, "f-score_" + pos.tag] = "{:.4f}".format(f1_scores.mean())
            
        print(df_scores.to_latex(escape=False))

if __name__ == "__main__":
    
    feature_categories = [feature_extraction.FeatureCategory.COOC_PAIR, feature_extraction.FeatureCategory.WEB1T_PATTERNS, feature_extraction.FeatureCategory.WORD_EMBED]
    # feature_categories = [feature_extraction.FeatureCategory.WEB1T_PATTERNS]
    # feature_categories.remove(feature_extraction.FeatureCategory.WORD_EMBED)
    # feature_categories.remove(feature_extraction.FeatureCategory.JB_SIM)
    # feature_categories.remove(feature_extraction.FeatureCategory.MORPH)
    # feature_categories.remove(feature_extraction.FeatureCategory.PATTERNS)
    
    # gre_to_classifier_tsv()
    # eval_turn(feature_categories)
    # eval_lqzq(feature_categories)
    
    # add_gold_prediction_gre()
    # accuracy_on_gre()
    
    # learn.extract_features_to_files(config.path_to_res("turn_testset"), [feature_extraction.FeatureCategory.PARA_COOC_PAIR])
    # learn.extract_features_to_files(config.path_to_res("lzqz_testset"), [feature_extraction.FeatureCategory.PARA_COOC_PAIR])
    
    # cross_val_turn()
    
    ablation_test_wn_data(False)
    
    # cross_val_wn(feature_categories)
    
    # single_categorie_test_wn(False)
    
    # compare_classifiers_wn_data()
    
    # fit_hyper_params_rf()
    
    # test_web1t_pruning()
