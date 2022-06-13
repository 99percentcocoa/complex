import logging
import pandas as pd
import numpy as np
import re
import google_sheets
from isc_parser import Parser
import handle
import data
import sys

logging.basicConfig(level=logging.DEBUG)

parser = Parser(lang='hin')

# ALL INDICES STARTING FROM 1, NOT 0

def write_output(all_output_series):

    # For OP1, OP2
    writeArray1 = []
    writeArray2 = [[], []]

    # headers
    writeArray1.append(['Sentence ID', 'Sentence', 'Clause 1 ID', 'Clause 1', 'Clause 2 ID', 'Clause 2', 'Connective'])
    writeArray2[0].extend(['ID'])
    writeArray2[1].extend(['Sentence'])

    for series in all_output_series:
        # For OP1
        writeArray1.append([series['original']['id'], series['original']['sentence'], series['c1']['id'], series['c1']['sentence'], series['c2']['id'], series['c2']['sentence'], series['connective']])

        # For OP2
        writeArray2[0].extend([series['c1']['id'], series['c2']['id']])
        writeArray2[1].extend([series['c1']['sentence'], series['c2']['sentence']])

    open('writeArray1.txt', 'w').write("\n".join(str(x) for x in writeArray1))
    open('writeArray2.txt', 'w').write("\n".join(str(x) for x in writeArray2))

    # create spreadsheet
    newSheetId = google_sheets.create_new_sheet(data.outputFolderId)

    google_sheets.update_sheet_values(newSheetId, "Output1!A1:G", writeArray1, "ROWS")
    google_sheets.update_sheet_values(newSheetId, "Output2!A1:G", writeArray2, "COLUMNS")
    # logging.info(writeArray1)
    # logging.info(writeArray2)


def main(corpus_sheet_name):

    sentencesdf = data.get_sentences(corpus_sheet_name)
    # clean sentences
    sentencesdf['sentence'] = sentencesdf['sentence'].apply(lambda x: handle.clean_sentences(x))
    totalSentences = len(sentencesdf)
    connectiveClassesdf = data.connectiveClassesdf

    all_output_series = []
    for index, row in sentencesdf.iterrows():
        id = row['id']
        sentence = row['sentence']
        logging.info(f'{index+1}/{totalSentences}: At {id}: {sentence}')
        sentenceArray = sentence.split(' ')

        parserOutput = parser.parse(sentenceArray)

        sentencedf = pd.DataFrame([[row[i] for i in [2, 3, 6, 7]] for row in parserOutput], columns=['word', 'type', 'dep_num', 'dep'], index=range(1, len(parserOutput)+1))
        # logging.info(sentencedf)
        
        connectivesdf = sentencedf.drop(['type', 'dep', 'dep_num'], axis=1).reset_index().merge(connectiveClassesdf.drop('substitution', axis=1), left_on=["word"], right_on=["connective"]).set_index('index').reset_index().rename(columns={'index':'position'}).drop(['word'], axis=1)
        # logging.info(connectivesdf)

        # for c_index, c_row in connectivesdf.iterrows():
        if len(connectivesdf.index) == 0:
            logging.info("No connectives. Skipping.")
            continue

        c_row = connectivesdf.iloc[0]

        connective_type = c_row['type']

        # temporary: types not supported yet.
        if int(connective_type) not in (1, 2, 4):
            logging.info(f'Type {connective_type} not supported. Skipping.')
            continue

        position = int(c_row['position'])

        # no VM found in clause 1.
        if 'VM' not in sentencedf.iloc[:position-1]['type'].to_list():
            logging.info('No VM found in clause 1. Skipping.')
            continue

        handlerFunction = getattr(handle, ''.join(('handle', str(connective_type))))

        # for printing output to google sheets
        output_series = handlerFunction(id, sentencedf, position)

        if output_series.empty:
            continue

        all_output_series.append(output_series)

        logging.info(f"appended to output: {output_series['c1']['sentence']}, {output_series['c2']['sentence']}")
        # write_single(output_series)
        logging.info("At end of iteration.")
    
    write_output(all_output_series)

if __name__ == '__main__':
    try:
        corpus_sheet_name = sys.argv[1]
    except IndexError:
        corpus_sheet_name = 'Sheet1'
    
    main(corpus_sheet_name)