from __future__ import print_function
import logging
logging.basicConfig(level=logging.DEBUG)

import os.path
import string
from datetime import datetime
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# The ID and range of a sample spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1ZGXKNdNmua9X5TsRwebrjZxoOJOXc0ZJymaoO_BkS8Q'
# SAMPLE_RANGE_NAME = 'Sheet1!A1:C'

def get_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_sheet_values(sheet_id, range):
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id,
                                    range=range).execute()
        values = result.get('values', [])
        toRet = []

        if not values:
            print('No data found.')
            return

        alphabet = string.ascii_uppercase[:26]
        rangeSplit = range.split('!')[1].split(':')
        numCols =  alphabet.index(rangeSplit[1][0])-alphabet.index(rangeSplit[0][0])+1

        for row in values:
            temp = row
            while len(temp) < numCols:
                temp.append('')
            toRet.append(temp)
        
        return toRet

    except HttpError as err:
        print(err)

def update_sheet_values(sheet_id, range, valuesArray, majorDimension):
    try:
        service = build('sheets', 'v4', credentials=get_creds())
        sheet = service.spreadsheets()

        valueRangeBody = {
            "range": range,
            "majorDimension": majorDimension,
            "values": valuesArray
        }

        request = sheet.values().update(spreadsheetId=sheet_id, range=range, valueInputOption='RAW', body=valueRangeBody)
        response = request.execute()

    except HttpError as err:
        print(err)

def append_to_sheet(sheet_id, range, valuesArray, majorDimension):
    try:
        service = build('sheets', 'v4', credentials=get_creds())
        sheet = service.spreadsheets()

        valueRangeBody = {
            "range": range,
            "majorDimension": majorDimension,
            "values": valuesArray
        }

        request = sheet.values().append(spreadsheetId=sheet_id, range=range, valueInputOption='RAW', body=valueRangeBody)
        response = request.execute()

    except HttpError as err:
        print(err)

# creates sheet in Folder ID according to predefined format, returns file ID
def create_new_sheet(folder_id):
    file_metadata = {
        'name': ' '.join(('Output', datetime.now().strftime("%d-%m-%y %H:%M"))),
        'parents': [folder_id],
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }

    try:
        credentials = get_creds()
        service = build('drive', 'v3', credentials=credentials)
        sheet = service.files().create(body=file_metadata).execute()
        add_sheets(sheet['id'], credentials)

        return sheet['id']
    
    except HttpError as err:
        print(err)
        return None

# adds sheets "Output1" and "Output2" to sheet, removes "Sheet1"
def add_sheets(sheetId, credentials):

    batch_update_body = {
        'requests': [
            {
                "addSheet": {
                    "properties": {
                        "title": "Output1"
                    }
                }
            },
            {
                "addSheet": {
                    "properties": {
                        "title": "Output2"
                    }
                }
            },
            {
                "addSheet": {
                    "properties": {
                        "title": "Log"
                    }
                }
            },
            {
                "deleteSheet": {
                    "sheetId": 0
                }
            }
        ]
    }

    try:
        service = build('sheets', 'v4', credentials=credentials)

        req = service.spreadsheets().batchUpdate(spreadsheetId=sheetId, body=batch_update_body)
        res = req.execute()

    except HttpError as err:
        print(err)
        return None

def write_df_to_sheet(df, sheet_id, range):
    try:
        service = build('sheets', 'v4', credentials=get_creds())
        sheet = service.spreadsheets()

        valueRangeBody = {
            "range": range,
            "majorDimension": "ROWS",
            "values": pd.concat([df.columns.to_frame().T, df], ignore_index=True).to_numpy().tolist()
        }

        request = sheet.values().append(spreadsheetId=sheet_id, range=range, valueInputOption='RAW', body=valueRangeBody)
        response = request.execute()

    except HttpError as err:
        print(err)