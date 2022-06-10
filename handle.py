import pandas as pd
import numpy as np
import re
import data

def removePunctuation(s):
    return re.sub('[,।?!]', '', s)

# takes input as series (row of sentencesdf)
# returns series containing connective, and two series for each clause

"""
1 -> Vakya Karma
2 -> Coordinate
3 -> Subordinate
4 -> Relative
"""

def handle1(series, position):
    sentenceID = series[0]
    arr = series[1].split(' ')
    connective = arr[position-1]
    c1 = pd.Series(data=[''.join((sentenceID, '.1')), ' '.join(arr[:position-1])], index=['id', 'sentence'])
    c2 = pd.Series(data=[''.join((sentenceID, '.2')), ' '.join(arr[position:])], index=['id', 'sentence'])
    # sid1 = ''.join((sentenceID, '.1'))
    # sid2 = ''.join((sentenceID, '.2'))
    output = pd.Series(data=[series, c1, c2, connective], index=['original', 'c1', 'c2', 'connective'])
    return output

def handle4(series, position):
    sentenceID = series[0]
    arr = series[1].split(' ')
    connective = arr[position-1]
    substitution = data.connectiveClassesdf.loc[data.connectiveClassesdf['connective'] == connective]['substitution'].iat[0]
    # print(arr)
    # print(' '.join(arr[:position-1]))
    c1 = pd.Series(data=[''.join((sentenceID, '.1')), ' '.join(arr[:position-1])], index=['id', 'sentence'])
    c2 = pd.Series(data=[''.join((sentenceID, '.2')), ' '.join(np.concatenate(([substitution], arr[position:])).tolist())], index=['id', 'sentence'])
    output = pd.Series(data=[series, c1, c2, connective], index=['original', 'c1', 'c2', 'connective'])
    return output


# if __name__ == "__main__":
#     series = pd.Series({'id': 'Hin_Geo_ncert_6stnd_1ch_0072', 'sentence': 'यही कारण है कि इसके आकार को भू-आभ कहा जाता है।'})
#     print(handle1(series, 4)['c2']['sentence'])