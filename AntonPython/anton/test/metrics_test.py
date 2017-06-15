'''
Created on Feb 29, 2016

@author: peter
'''
from sklearn.metrics import f1_score
y_true = [1, 1, 1, 1, 1, 1, 1, 1, 1, 2]
y_pred = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

print(f1_score(y_true, y_pred, average='macro'))  
print(f1_score(y_true, y_pred, average='micro'))  
print(f1_score(y_true, y_pred, average='weighted')) 