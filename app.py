
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
from plotly.subplots import make_subplots
import os
import shutil
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import lxml
import lxml.etree as ET
from datetime import datetime
from datetime import timedelta

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# # Given a folder path extract all the head files
def genFolderDict(folderpath):

    folderDict = {}

    root, dirs, files = next(os.walk(folderPath))

    for folder in dirs:

        # extract the key pile info from a given head file object
        pileDict = extractPileInfo(folder)

        # append pile dictionary to all folders dictionary, folder name as key
        folderDict[folder] = pileDict

    return folderDict

# Given a record number extract all the key pile info from the head file
def extractPileInfo(record_num):

    headFile = '/head.pdex'

    tree = ET.parse(folderPath+record_num+headFile)
    head = tree.getroot()

    pileNumber = head.xpath('.//Tag[text()="pile number"]')[0].getnext().text
    startTime = datetime.strptime(head.xpath('.//StartTime')[0].text, '%Y-%m-%dT%H:%M:%S')
    stopTime = datetime.strptime(head.xpath('.//StopTime')[0].text, '%Y-%m-%dT%H:%M:%S')
    duration = str(stopTime-startTime)
    maxDepth = float(head.xpath('.//Tag[text()="maximum depth"]')[0].getnext().text)/100
    concVol = float(head.xpath('.//Tag[text()="concrete volume pile"]')[0].getnext().text)

    pileDict = {'pile number': pileNumber,
                'start date': startTime.date(),
                'duration': duration,
                'max depth': maxDepth,
                'concrete volume': concVol}

    return pileDict

# Given a date and pile number extract QA info
def extractPileQA(pile_number, start_date):

    pileQA = df_QA_key[(df_QA_key['Pile Number'] == pile_number) & (df_QA_key['Completion Date:'] == start_date)]

    return pileQA

# Generate production piles
def generateProdPiles():

    df_allPiles= pd.DataFrame.from_dict(folderDict, orient='index')

    df_allPiles= df_allPiles[df_allPiles['concrete volume'] != 0]

    pileStatus = []
    pileType = []
    for index, row in df_allPiles.iterrows():
        pileQA = extractPileQA(row['pile number'], row['start date'])

        if pileQA.empty:
            qa_status = ['NO RECORD', 'NO RECORD']
        elif pileQA.size > 10:
            for i, r in pileQA.iterrows():
                if r['Pile Status '] == 'Production':
                    qa_status = [r['Pile Status '], r['Design: Design Type']]
        else:
            for i, r in pileQA.iterrows():
                qa_status = [r['Pile Status '], r['Design: Design Type']]
        pileStatus.append(qa_status[0])
        pileType.append(qa_status[1])

    df_allPiles['pile status'] = pileStatus
    df_allPiles['pile type'] = pileType

    df_allPiles = df_allPiles[df_allPiles['pile status'] != 'Re-Drilled']

    return df_allPiles

folderPath = 'C:/Users/bilel/Dropbox/ACTIVE/Waiari/LB24 Data - Clean/'

# Extract all the key pile info for each folder in the folder path
folderDict = genFolderDict(folderPath)

# Import QA file
df_QA = pd.read_csv('C:/Users/bilel/Dropbox/ACTIVE/Waiari/QA CFA Record.csv')

df_QA['Completion Date:'] = pd.to_datetime(df_QA['Completion Date:'], format='%d/%m/%Y').dt.date

df_QA_key = df_QA[['Completion Date:',
                   'Pile Number',
                   'Pile Status ',
                   'Design: Design Type',
                   'As-Built: Drill Depth (m):',
                   'Actual Volume (m3):',
                   'Dif Volume (m3):',
                   'Comments/Delays',
                   'Obstructions Encountered',
                   'Probing Record (depth relative to 8.3mRL)']]

prodPiles = generateProdPiles()
prodPiles = prodPiles.groupby('start date')['max depth'].sum().reset_index()

fig = go.Figure(data=[go.Bar(x=prodPiles['start date'],
                             y=prodPiles['max depth'],
                             text=prodPiles['max depth'],
                             textposition='auto')])

# Define the dash app layout
app.layout = html.Div(children=[
    dcc.Graph(
        id='basic-interactions',
        figure=fig
    )]
)

if __name__ == '__main__':
    app.run_server()
