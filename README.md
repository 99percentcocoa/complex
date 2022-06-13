# README

## Links to resources

The program uses three Google Sheets Spreadsheets:

	a. Test Corpus Sheet - this sheet contains the sentence IDs and sentences required to be processed. This spreadsheet can contain multiple sheets, and the user can choose which sheet to run the program on (see Instructions).

	b. Connective Classes Sheet - this sheet contains the list of connectives, and what class/type they belong to.
	
	c. Output Sheet Folder - Folder where the Output Sheet will be stored - this spreadsheet will contain the output once generated. It will have two sheets, "Output1" and "Output2".

The file data.py contains links to these three items in the form of file IDs. File IDs are a part of the URL of the spreadsheet.
For example, suppose the URL of the spreadsheet is [https://docs.google.com/spreadsheets/d/14aIDFRs3ThMt10pRZsRPeLwapwl698hG7xswu2E_U0E/edit#gid=0].
The file ID is the string between "d/" and "/edit", i.e., "14aIDFRs3ThMt10pRZsRPeLwapwl698hG7xswu2E_U0E" here.

Check the file IDs in data.py, and change if required.

* * *

INSTRUCTIONS

Navigate to the folder containing all the files, and run main.py:
$ python3 main.py [test_sheet_name]

[test_sheet_name] is the name of the sheet inside the Test Corpus spreadsheet, which is to be used. If none is specified, "Sheet1" will be used by default.


NOTE: Google Authentication

To enable reading and writing to spreadsheets, Google Authentication is required. The first time main.py is run, an authentication link will be prompted in the terminal. Open the link, and follow the instructions. This will only happen once.