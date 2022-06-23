import pandas as pd
import numpy as np
import re
import data
import logging
from isc_parser import Parser

parser = Parser(lang='hin')

def removePunctuation(s):
    return re.sub('[,।?!]', '', s)

def parse(s):
    return np.array(parser.parse(s.split(' ')))

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

connectiveClassesdf = data.connectiveClassesdf

# create a sentence df from a sentence
def create_sdf(sentence):
    sentence = clean_sentences(sentence)
    parserOutput = parse(sentence)
    sentencedf = pd.DataFrame([[row[i] for i in [2, 3, 6, 7]] for row in parserOutput], columns=['word', 'type', 'dep_num', 'dep'], index=range(1, len(parserOutput)+1))
    return sentencedf

# create connectives df from sentence df
def create_cdf(sdf):
    cdf = sdf.drop(['type', 'dep', 'dep_num'], axis=1).reset_index().merge(connectiveClassesdf.drop('substitution', axis=1), left_on=["word"], right_on=["connective"]).set_index('index').reset_index().rename(columns={'index':'position'}).drop(['word'], axis=1).sort_values(by='position')
    return cdf

# return pd array containing common info, so don't have to declare each time.
def getInfo(sdf, position):
    arr = sdf['word'].to_list()
    sentence = ' '.join(w for w in arr)

    # check if WQ in clause1, give final punctuation accordingly
    finalPunctuation = arr[-1]
    if 'WQ' in sdf.loc[:position]['type'].to_list():
        finalPunctuation = '?'

    return pd.Series([sentence, finalPunctuation, arr, arr[position-1]], index=['sentence', 'finalPunctuation', 'arr', 'connective'])

# create clause ids
def assign_ids(id, arr):
    if len(arr) == 0:
        return []
    else:
        ids = []
        for i in range(1, len(arr)+1):
            ids.append('-'.join((id, str(i))))
        return ids


# checking conditions, used in handle functions

# checks whether 'VM' present in 1st clause
# arguments (sdf, position), output True/False
def check_vm(sdf, position):
    if 'VM' in sdf.loc[:position]['type'].to_list():
        logging.info(f"VM found at {sdf[sdf['type'] == 'VM']['word'].to_list()}")
        return True
    else:
        logging.info('No VM found in clause 1. Skipping.')
        return False

# lookup subsitution: takes connecive as input, returns substitution. Ensure input is of correct type.
def lookup_connective_substitution(connective):
    substitution = data.connectiveClassesdf.loc[data.connectiveClassesdf['connective'] == connective]['substitution'].iat[0]
    return substitution

# lookup karta substitution: takes (sdf, position) as input, returns first found karta in clause 1.
# if not found, returns empty array
def lookup_karta_substitution(sdf, position):
    sdf_clause1 = sdf[:position-1]
    # note: returns 1st found karta
    try:
        substitution = sdf_clause1[sdf_clause1['dep'] == 'k1'].iloc[0]['word']
        return substitution
    except IndexError as err:
        return []

# given sdf and position, check if both clauses have a ccof pointing to connector position
def check_ccof(sdf, position):
    sdf_clause1 = sdf.loc[:position-1]
    sdf_clause2 = sdf.loc[position+1:]
    return bool(len(sdf_clause1[(sdf_clause1['dep_num'] == str(position)) & (sdf_clause1['dep'] == "ccof")]) > 0) or bool(len(sdf_clause2[(sdf_clause2['dep_num'] == str(position)) & (sdf_clause2['dep'] == "ccof")]) > 0)


def handle1(sdf, position):

    sentenceInfo = getInfo(sdf, position)

    if not check_vm(sdf, position):
        return []

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip(','), sentenceInfo.finalPunctuation))
    c1 = c1_final
    c2 = ' '.join(sentenceInfo.arr[position:])

    output = [c1, c2]
    return output


def handle2(sdf, position):

    sentenceInfo = getInfo(sdf, position)

    # check if both sides ccof
    if check_ccof(sdf, position):
        return []
    
    if not check_vm(sdf, position):
        return []

    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip(','), sentenceInfo.finalPunctuation))

    # first karta
    substitution = lookup_karta_substitution(sdf, position)
    if not bool(substitution):
        return []
    
    c2_sentence = ' '.join(sentenceInfo.arr[position:])
    c2_final = ' '.join((substitution, c2_sentence))

    c1 = c1_final
    c2 = c2_final

    output = [c1, c2]
    return output

def handle4(sdf, position):
    sentenceInfo = getInfo(sdf, position)

    if not check_vm(sdf, position):
        return []
    
    substitution = lookup_connective_substitution(sentenceInfo.connective)

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip(','), sentenceInfo.finalPunctuation))
    c1 = c1_final
    c2 = ' '.join(np.concatenate(([substitution], sentenceInfo.arr[position:])).tolist())
    output = [c1, c2]
    return output