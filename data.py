import google_sheets
import pandas as pd
import re

def removePunctuation(s):
    return re.sub('[,।?!]', '', s)

testCorpusSheetId = "14aIDFRs3ThMt10pRZsRPeLwapwl698hG7xswu2E_U0E"
connectiveClassesSheetId = "1ZGXKNdNmua9X5TsRwebrjZxoOJOXc0ZJymaoO_BkS8Q"
outputFolderId = "1v2DpNms30OJZUVt_V533QrnCWvLWNdAY"

connectiveClasses = google_sheets.get_sheet_values(connectiveClassesSheetId, "Sheet1!A1:C")
connectiveClassesdf = pd.DataFrame(connectiveClasses[1:], columns=connectiveClasses[0], index=range(1, len(connectiveClasses)))
connectiveClassesdf.type = pd.to_numeric(connectiveClassesdf.type).fillna(0).astype('Int64')

def get_sentences(corpus_sheet_name):
    sentences = google_sheets.get_sheet_values(testCorpusSheetId, '!'.join((corpus_sheet_name, 'A1:B')))
    sentencesdf = pd.DataFrame(sentences[1:], columns=sentences[0], index=range(1, len(sentences)))
    # sentencesdf['sentence'] = sentencesdf['sentence'].apply(removePunctuation)

    return sentencesdf