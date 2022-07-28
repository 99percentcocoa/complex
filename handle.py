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
connectives = connectiveClassesdf['connective'].to_list()

# create a sentence df from a sentence
def create_sdf(sentence):
    sentence = clean_sentences(sentence)
    parserOutput = parse(sentence)
    sentencedf = pd.DataFrame([[row[i] for i in [2, 3, 6, 7]] for row in parserOutput], columns=['word', 'type', 'dep_num', 'dep'], index=range(1, len(parserOutput)+1))
    return sentencedf

# function that converts character-indexed positions to word-indexed positions. Used by create_cdf.
def getPositions(c, s):
    cArray = c.split(' ')
    sArray = s.split(' ')
    posArray = []

    for w in cArray:
        posArray.append(sArray.index(w)+1)
    
    return posArray

# create connectives df from sentence df
def create_cdf(sdf):
    sentence = ' '.join(sdf['word'].to_list())
    matches = []
    for c in connectives:
        regstr = '(?<=[ .,?!])' + c + '(?=[ .,?!])'
        for match in re.finditer(regstr, sentence):
            matchInfo = [match.group(0), set(np.arange(match.start(), match.end()))]
            # print(matchInfo)
            matches.append(matchInfo)
    # sort by length
    matches = sorted(matches, key=lambda m: -len(m[1]))
    # print(f'matches: {matches}')
    uniqueMatches = matches

    # go through, compare
    for i in list(range(len(uniqueMatches))):
        # print(f'i: {i}')
        for e in uniqueMatches[i+1:]:
            if e[1].issubset(uniqueMatches[i][1]):
                uniqueMatches.remove(e)

    # sort unique matches by position
    uniqueMatches = sorted(uniqueMatches, key=lambda m: list(m[1])[0])
    print(uniqueMatches)

    connectiveStrings = list(map(lambda x: x[0], uniqueMatches))
    # print(connectiveStrings)

    connectivePositions = list(map(lambda x: getPositions(x, sentence), connectiveStrings))
    # print(connectivePositions)

    ccdf = pd.DataFrame(data={'position': connectivePositions, 'connective': connectiveStrings, 'type': [connectiveClassesdf.iloc[connectives.index(x)]['type'] for x in connectiveStrings]})
    return ccdf

# return pd array containing common info, so don't have to declare each time.
def getInfo(sdf, position):
    arr = sdf['word'].to_list()
    sentence = ' '.join(w for w in arr)

    # check if WQ in clause1, give final punctuation accordingly
    finalPunctuation = arr[-1]
    if 'WQ' in sdf.loc[:position[0]]['type'].to_list():
        finalPunctuation = '?'

    return pd.Series([sentence, finalPunctuation, arr, ' '.join([arr[i-1] for i in position])], index=['sentence', 'finalPunctuation', 'arr', 'connective'])

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
    if 'VM' in sdf.loc[:position[0]]['type'].to_list():
        logging.info(f"VM found at {sdf[sdf['type'] == 'VM']['word'].to_list()}")
        return True
    else:
        logging.info('No VM found in clause 1. Skipping.')
        return False

# lookup subsitution: takes connecive as input, returns substitution. Ensure input is of correct type.
def lookup_connective_substitution(connective):
    """Lookup connective substitution
    
    >>> lookup_connective_substitution('जिसने')
    'इसने'
    >>> lookup_connective_substitution('परन्तु')
    ''
    >>> lookup_connective_substitution('जो कि')
    'वह'
    """
    substitution = data.connectiveClassesdf.loc[data.connectiveClassesdf['connective'] == connective]['substitution'].iat[0]
    return substitution

# lookup karta substitution: takes (sdf, position) as input, returns first found karta in clause 1.
# if not found, returns empty array
def lookup_karta_substitution(sdf, position):
    sdf_clause1 = sdf[:position[0]-1]
    # note: returns 1st found karta
    try:
        substitution = sdf_clause1[sdf_clause1['dep'] == 'k1'].iloc[0]['word']
        return substitution
    except IndexError as err:
        return []

# given sdf and position, check if both clauses have a ccof pointing to connector position
def check_ccof(sdf, position):
    sdf_clause1 = sdf.loc[:position[0]-1]
    sdf_clause2 = sdf.loc[position[-1]+1:]
    return bool(len(sdf_clause1[(sdf_clause1['dep_num'] == str(position[0])) & (sdf_clause1['dep'] == "ccof")]) > 0) or bool(len(sdf_clause2[(sdf_clause2['dep_num'] == str(position[0])) & (sdf_clause2['dep'] == "ccof")]) > 0)


def handle1(sdf, position):
    # position is an array. For type 1, it will have only 1 element

    sentenceInfo = getInfo(sdf, position)

    if not check_vm(sdf, position):
        return []

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position[0]-1])
    c1_final = ' '.join((c1_sentence.strip(','), sentenceInfo.finalPunctuation))
    c1 = c1_final
    c2 = ' '.join(sentenceInfo.arr[position[0]:])

    output = [c1, c2]
    return output


def handle2(sdf, position):

    sentenceInfo = getInfo(sdf, position)

    # check if both sides ccof
    if check_ccof(sdf, position):
        print('ccof check failed.')
        return []
    
    if not check_vm(sdf, position):
        print('vm check failed.')
        return []

    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip(','), sentenceInfo.finalPunctuation))

    # first karta
    substitution = lookup_karta_substitution(sdf, position)
    print(f'Substitution: {substitution}')
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
    c1_sentence = ' '.join(sentenceInfo.arr[:position[0]-1])
    c1_final = ' '.join((c1_sentence.strip(','), sentenceInfo.finalPunctuation))
    c1 = c1_final
    c2 = ' '.join(np.concatenate(([substitution], sentenceInfo.arr[position[-1]:])).tolist())
    output = [c1, c2]
    return output

# doctest code
if __name__ == "__main__":
    import doctest
    doctest.testmod()