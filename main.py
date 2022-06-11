import logging
import pandas as pd
import numpy as np
import re
import google_sheets
from isc_parser import Parser
import handle
import data

logging.basicConfig(level=logging.DEBUG)

parser = Parser(lang='hin')

# ALL INDICES STARTING FROM 1, NOT 0

sentencesdf = data.sentencesdf
# clean sentences
sentencesdf['sentence'] = sentencesdf['sentence'].apply(lambda x: handle.clean_sentences(x))
connectiveClassesdf = data.connectiveClassesdf

def write_output(all_output_series):

    # For OP1, OP2
    writeArray1 = []
    writeArray2 = [[], []]

    for series in all_output_series:
        # For OP1
        writeArray1.append([series['original']['id'], series['original']['sentence'], series['c1']['id'], series['c1']['sentence'], series['c2']['id'], series['c2']['sentence'], series['connective']])

        # For OP2
        writeArray2[0].extend([series['c1']['id'], series['c2']['id']])
        writeArray2[1].extend([series['c1']['sentence'], series['c2']['sentence']])

    open('writeArray1.txt', 'w').write("\n".join(str(x) for x in writeArray1))
    open('writeArray2.txt', 'w').write("\n".join(str(x) for x in writeArray2))
    google_sheets.update_sheet_values(data.outputSheetId, "Output1!A2:G", writeArray1, "ROWS")
    google_sheets.update_sheet_values(data.outputSheetId, "Output2!A2:G", writeArray2, "COLUMNS")
    # logging.info(writeArray1)
    # logging.info(writeArray2)


def write_single(output_series):
    writeArray1 = output_series['original']['id'], output_series['original']['sentence'], output_series['c1']['id'], output_series['c1']['sentence'], output_series['c2']['id'], output_series['c2']['sentence'], output_series['connective']
    writeArray2 = [[output_series['c1']['id'], output_series['c2']['id']], [output_series['c1']['sentence'], output_series['c2']['sentence']]]

    google_sheets.append_to_sheet(data.outputSheetId, "Output1!A2:G", writeArray1, "ROWS")
    google_sheets.append_to_sheet(data.outputSheetId, "Output2!A2:G", writeArray2, "COLUMNS")

# iterate over sentences df

def main():
    all_output_series = []
    for index, row in sentencesdf.iterrows():
        id = row['id']
        sentence = row['sentence']
        logging.info(f'At {id}: {sentence}')
        sentenceArray = sentence.split(' ')

        parserOutput = parser.parse(sentenceArray)

        sentencedf = pd.DataFrame([row[2:4] for row in parserOutput], columns=['word', 'type'], index=range(1, len(parserOutput)+1))
        # logging.info(sentencedf)
        
        connectivesdf = sentencedf.drop('type', axis=1).reset_index().merge(data.connectiveClassesdf.drop('substitution', axis=1), left_on=["word"], right_on=["connective"]).set_index('index').reset_index().rename(columns={'index':'position'}).drop(['word'], axis=1)
        # logging.info(connectivesdf)

        # for c_index, c_row in connectivesdf.iterrows():
        if len(connectivesdf.index) == 0:
            logging.info("No connectives. Skipping.")
            continue
        c_row = connectivesdf.iloc[0]
        connective_type = c_row['type']

        # temporary: types not supported yet.
        if int(connective_type) not in (1, 4):
            logging.info(f'Type {connective_type} not supported. Skipping.')
            continue

        position = int(c_row['position'])

        # no VM found in clause 1.
        if 'VM' not in sentencedf.iloc[:position-1]['type'].to_list():
            logging.info('No VM found in clause 1. Skipping.')
            continue

        handlerFunction = getattr(handle, ''.join(('handle', str(connective_type))))

        # for printing output to google sheets
        output_series = handlerFunction(row, position)
        all_output_series.append(output_series)

        logging.info(f"appended to output: {output_series['c1']['sentence']}, {output_series['c2']['sentence']}")
        # write_single(output_series)
        logging.info("At end of iteration.")
    
    write_output(all_output_series)

if __name__ == '__main__':
    main()