from __future__ import print_function
import logging
logging.basicConfig(level=logging.DEBUG)

import os.path
import string
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

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