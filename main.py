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

def write_output(op1df, op2df):

    open('writeArray1.txt', 'w').write(pd.concat([op1df.columns.to_frame().T, op1df], ignore_index=True).to_string())
    open('writeArray2.txt', 'w').write(pd.concat([op2df.columns.to_frame().T, op2df], ignore_index=True).to_string())

    # create spreadsheet
    newSheetId = google_sheets.create_new_sheet(data.outputFolderId)

    google_sheets.write_df_to_sheet(op1df, newSheetId, "Output1!A1:E")
    google_sheets.write_df_to_sheet(op2df, newSheetId, "Output2!A1:B")
    # google_sheets.update_sheet_values(newSheetId, "Output1!A1:G", writeArray1, "ROWS")
    # google_sheets.update_sheet_values(newSheetId, "Output2!A1:G", writeArray2, "COLUMNS")
    # logging.info(writeArray1)
    # logging.info(writeArray2)


def main(corpus_sheet_name):

    sentencesdf = data.get_sentences(corpus_sheet_name)
    sentencesdf['sentence'] = sentencesdf['sentence'].apply(lambda x: handle.clean_sentences(x))

    all_output_series = []
    op2df = pd.DataFrame(data=[], columns=['ID', 'Sentence'])
    op1df = pd.DataFrame(data=[], columns=['Original ID', 'Original Sentence', 'Clause IDs', 'Clauses', 'Connectives'])

    for idx, row in sentencesdf.iterrows():
        outputSentences = []
        connectives = []
        logging.info(f"At {row['sentence']}")
        inputSentence = row['sentence']
        id = row['id']

        # initial sdf, cdf
        sdf = handle.create_sdf(inputSentence)
        cdf = handle.create_cdf(sdf)

        while len(cdf) > 0:
            logging.info(f'cdf: {cdf}')
            position = int(cdf.iloc[0]['position'])
            c_type = int(cdf.iloc[0]['type'])
            connective = cdf.iloc[0]['connective']
            logging.info(f"Handling {connective} at position {position}")

            # unsupported type.
            if c_type not in (1, 2, 4):
                logging.info(f'{c_type}: unsupported type. Skipping.')
                cdf = cdf.drop(index=0).reset_index(drop=True)
                continue
            
            funcName = ''.join(('handle', str(c_type)))
            funcOutput = getattr(handle, funcName)(sdf, position)

            if len(funcOutput) == 0:
                # clauses not generated. Update cdf, move to next iteration. Keep sdf unchanged. Keep outputSentences unchanged.
                logging.info('Empty output. Skipping.')
                cdf = cdf.drop(index=0).reset_index(drop=True)
                # continue
            else:
                # clauses generated. Log to output array, regenerate sdf, regenerate cdf, move to next iteration.
                # If clauses generated, pop last element from outputSentences, add both new elements.
                logging.info(f'Func output: {funcOutput}')

                if len(outputSentences) > 0:
                    outputSentences.pop(-1)
                outputSentences.extend(funcOutput)

                connectives.append(connective)
                
                sdf = handle.create_sdf(funcOutput[1])
                cdf = handle.create_cdf(sdf)

            # logging.info(len(cdf))
        outputSentences = pd.Series(data=outputSentences).drop_duplicates().to_list()
        logging.info(f'output sentences: {outputSentences}')
        logging.info(f'connectives: {connectives}')
        clauseIDs = handle.assign_ids(id, outputSentences)
        logging.info(clauseIDs)
        # logging.info(generate_sentences_df(outputSentences, clauseIDs))

        # append to output dataframes
        op2Sentencedf = pd.DataFrame(data={'ID': clauseIDs, 'Sentence': outputSentences})
        op2df = pd.concat([op2df, op2Sentencedf], axis=0, ignore_index=True)
        op1df.loc[len(op1df)] = [id, inputSentence, '\n'.join(clauseIDs), '\n'.join(outputSentences), '\n'.join(connectives)]
        
    write_output(op1df, op2df)

if __name__ == '__main__':
    try:
        corpus_sheet_name = sys.argv[1]
    except IndexError:
        corpus_sheet_name = 'Sheet1'
    
    main(corpus_sheet_name)