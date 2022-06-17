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

    return pd.Series([sentence, arr[-1], arr, arr[position-1]], index=['sentence', 'finalPunctuation', 'arr', 'connective'])

# create clause ids
def assign_ids(id, arr):
    if len(arr) == 0:
        return []
    else:
        ids = []
        for i in range(1, len(arr)+1):
            ids.append('-'.join((id, str(i))))
        return ids


def handle1(sdf, position):

    sentenceInfo = getInfo(sdf, position)

    sdfp1 = sdf.iloc[:position-1]
    if 'VM' not in sdfp1['type'].to_list():
        logging.info('No VM found in clause 1. Skipping.')
        return []

    logging.info(f"VM found at {sdfp1[sdfp1['type'] == 'VM']['word'].to_list()}")

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip().replace(',', ''), sentenceInfo.finalPunctuation))
    c1 = c1_final
    c2 = ' '.join(sentenceInfo.arr[position:])

    output = [c1, c2]
    return output


def handle2(sdf, position):

    sentenceInfo = getInfo(sdf, position)

    df_filtered = sdf.iloc[:position-1]
    if 'VM' not in df_filtered['type'].to_list():
        logging.info('No VM found in clause 1. Skipping.')
        return []

    logging.info(f"VM found at {df_filtered[df_filtered['type'] == 'VM']['word'].to_list()}")

    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence, sentenceInfo.finalPunctuation))

    # first karta
    try:
        substitution = df_filtered[df_filtered['dep'] == 'k1'].iloc[0]['word']
        logging.info(f'Substitution: {substitution}')
    except IndexError as err:
        logging.info('No k1 in c1. Skipping.')
        # return empty series
        return []
    
    c2_sentence = ' '.join(sentenceInfo.arr[position:])
    c2_final = ' '.join((substitution, c2_sentence))

    c1 = c1_final
    c2 = c2_final

    output = [c1, c2]
    return output

def handle4(sdf, position):
    sentenceInfo = getInfo(sdf, position)

    sdfp1 = sdf.iloc[:position-1]
    if 'VM' not in sdfp1['type'].to_list():
        logging.info('No VM found in clause 1. Skipping.')
        return []

    logging.info(f"VM found at {sdfp1[sdfp1['type'] == 'VM']['word'].to_list()}")
    
    substitution = data.connectiveClassesdf.loc[data.connectiveClassesdf['connective'] == sentenceInfo.connective]['substitution'].iat[0]

    # for c1, add same final punctuation symbol as c2
    c1_sentence = ' '.join(sentenceInfo.arr[:position-1])
    c1_final = ' '.join((c1_sentence.strip().replace(',', ''), sentenceInfo.finalPunctuation))
    c1 = c1_final
    c2 = ' '.join(np.concatenate(([substitution], sentenceInfo.arr[position:])).tolist())
    output = [c1, c2]
    return output


# if __name__ == "__main__":
#     series = pd.Series({'id': 'Hin_Geo_ncert_6stnd_1ch_0072', 'sentence': 'यही कारण है कि इसके आकार को भू-आभ कहा जाता है।'})
#     print(handle1(series, 4)['c2']['sentence'])