import handle
import logging
import data
import pandas as pd

logging.basicConfig(level=logging.DEBUG)

# returns string containing one or more id+sentence
def handle_single(sentence, id):

    sdf = handle.create_sdf(sentence)
    cdf = handle.create_cdf(sdf)

    outputSentences = []
    connectives = []

    # this while loop runs for a single sentence input
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
            # log_df = pd.concat([log_df, pd.DataFrame([[id, sentence, connective, c_type, position]], columns=['Sentence ID', 'Sentence', 'Connective', 'Type', 'Position'])], axis=0, ignore_index=True)
            cdf = cdf.drop(index=0).reset_index(drop=True)
        
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

    # check if output was generated, i.e. check if there is at least one split performed
    if len(connectives) > 0:
        outputSentences = pd.Series(data=outputSentences).to_list()
        logging.info(f'output sentences: {outputSentences}')
        logging.info(f'connectives: {connectives}')
        clauseIDs = handle.assign_ids(id, outputSentences)
        logging.info(clauseIDs)

        returnString = '\n'.join(['\t'.join((clauseIDs[i], outputSentences[i])) for i in list(range(len(clauseIDs)))])
        return returnString
    else:
        return '\t'.join((id, sentence))