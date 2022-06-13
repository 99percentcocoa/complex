import pandas as pd
import numpy as np
import re
import data

def removePunctuation(s):
    return re.sub('[,।?!]', '', s)

# cleaning function: take input string, gives output clean string - for use in dataframes
"""
Cleaning functions performed (in order):
    1. Strip whitespace from beginning and end.
    2. Replace multiple spaces with one space.
    3. Replace pipe symbols (|) with Hindi purna viram (।)
    4. Add space before final punctuation character.
    5. Ensure no space before comma
    6. Ensure space after comma.
    7. Add purna viram if no final punctuation.
"""
def clean_sentences(s):
    s = s.strip()
    s = re.sub('  +', ' ', s)
    s = s.replace('|', '।')
    s = re.sub(r'(?<![ ])[।?!]', r' \g<0>', s)
    s = re.sub(r'\s+(?=,)', r'', s)
    s = re.sub(r',(?! )', r', ', s)
    if not bool(re.search(r'[।?!]$', s)):
        s = ' '.join((s, '।'))
    return s

# takes input as series (row of sentencesdf)
# returns series containing connective, and two series for each clause

"""
1 -> Vakya Karma
2 -> Coordinate
3 -> Subordinate
4 -> Relative
"""

# return pd array containing common info, so don't have to declare each time.
def getInfo(id, sdf, position):
    arr = sdf['word'].to_list()
    sentence = ' '.join(w for w in arr)

    return pd.Series([id, sentence, arr[-1], arr, arr[position-1]], index=['sentenceID', 'sentence', 'finalPunctuation', 'arr', 'connective'])

def handle1(id, sdf, position):

    sentenceInfo = getInfo(id, sdf, position)
    series = pd.Series([id, sentenceInfo.sentence], index=['id', 'sentence'])

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip().replace(',', ''), sentenceInfo.finalPunctuation))
    c1 = pd.Series(data=[''.join((sentenceInfo.sentenceID, '.1')), c1_final], index=['id', 'sentence'])
    c2 = pd.Series(data=[''.join((sentenceInfo.sentenceID, '.2')), ' '.join(sentenceInfo.arr[position:])], index=['id', 'sentence'])

    output = pd.Series(data=[series, c1, c2, sentenceInfo.connective], index=['original', 'c1', 'c2', 'connective'])
    return output

def handle2(id, sdf, position):

    sentenceInfo = getInfo(id, sdf, position)
    series = pd.Series([id, sentenceInfo.sentence], index=['id', 'sentence'])

    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence, sentenceInfo.finalPunctuation))
    df_filtered = sdf[:position-1]

    # first karta
    subsitution = df_filtered[df_filtered['dep'] == 'k1'].iloc[0]['word']
    c2_sentence = ' '.join(sentenceInfo.arr[position:])
    c2_final = ' '.join((subsitution, c2_sentence))

    c1 = pd.Series(data=[''.join((sentenceInfo.sentenceID, '.1')), c1_final], index=['id', 'sentence'])
    c2 = pd.Series(data=[''.join((sentenceInfo.sentenceID, '.2')), ' '.join(sentenceInfo.arr[position:])], index=['id', 'sentence'])

    output = pd.Series(data=[series, c1, c2, sentenceInfo.connective], index=['original', 'c1', 'c2', 'connective'])
    return output

def handle4(id, sdf, position):
    sentenceInfo = getInfo(id, sdf, position)
    series = pd.Series([id, sentenceInfo.sentence], index=['id', 'sentence'])
    
    substitution = data.connectiveClassesdf.loc[data.connectiveClassesdf['connective'] == sentenceInfo.connective]['substitution'].iat[0]

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip().replace(',', ''), sentenceInfo.finalPunctuation))
    c1 = pd.Series(data=[''.join((sentenceInfo.sentenceID, '.1')), c1_final], index=['id', 'sentence'])
    c2 = pd.Series(data=[''.join((sentenceInfo.sentenceID, '.2')), ' '.join(np.concatenate(([substitution], sentenceInfo.arr[position:])).tolist())], index=['id', 'sentence'])
    output = pd.Series(data=[series, c1, c2, sentenceInfo.connective], index=['original', 'c1', 'c2', 'connective'])
    return output


# if __name__ == "__main__":
#     series = pd.Series({'id': 'Hin_Geo_ncert_6stnd_1ch_0072', 'sentence': 'यही कारण है कि इसके आकार को भू-आभ कहा जाता है।'})
#     print(handle1(series, 4)['c2']['sentence'])