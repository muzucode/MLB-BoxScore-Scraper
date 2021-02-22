import requests
import re
import pandas as pd
from selenium import webdriver
import html5lib
from bs4 import BeautifulSoup
pd.set_option('display.max_columns', 6)
pd.set_option('display.width', 1000)
import lxml
# Status: planning phase
def getLeague():

    URL = 'https://www.baseball-reference.com/leagues/MLB/2018-schedule.shtml'
    page = requests.get(URL)
    response = page.text
    extensions = []

    # Write to file
    # file = open('league_staging.html', 'w')
    # file.write(response)
    # file.close()

    # Create substring of the boxes element
    ss = '&nbsp;&nbsp;&nbsp;&nbsp;<em><a href="/boxes'
    matches = re.finditer(ss, response)
    matches_positions = [match.start() for match in matches]

    counter = 0

    for i in range(len(matches_positions)):
        counter+=1
        ind = matches_positions[i]
        line= response[ind:ind+66]
        extensions.append(line[38:])
        print('Box score: %s' % i, extensions[i])
        if counter == 10:
          break

    return extensions

def getBox():
    # Get all URL path extensions for boxscores
    extensions = getLeague()

    # Cycle through all the extensions passed over
    counter = 0
    for i in range(len(extensions)):
        URL = 'https://www.baseball-reference.com/%s' % extensions[i]
        source = requests.get(URL)

        # Remove the comment markers (tables are commented on get request)
        source = source.text
        source = source.replace("<!--", "")
        source = source.replace("-->", "")

        # Get away and home team for dynamic design
        def getTeams():
            # Search for <title> to dynamically assign team variables
            ss1 = '<title>'
            ss2 = '</title>'
            matches1 = re.finditer(ss1, source)
            matches_positions1 = [match.start() for match in matches1]
            matches2 = re.finditer(ss2, source)
            matches_positions2 = [match.start() for match in matches2]

            ind1 = matches_positions1[0]
            ind2 = matches_positions2[0]
            # X = entire title code
            x = source[ind1 + 7:ind2]
            # Clean up title code for indexing
            x = x.replace('at', '@')
            x = x.replace(' ', '')
            x = x.replace('.','')
            y = x.index('@')
            z = x.index('BoxScore')
            awayTeam = x[0:y]
            homeTeam = x[y + 1:z]
            return [awayTeam, homeTeam]

        teams = getTeams()
        print(teams)
        tables = []
        awayBatting = pd.read_html(source, attrs = {'id': '%sbatting' % teams[0]})
        homeBatting = pd.read_html(source, attrs = {'id': '%sbatting' % teams[1]})
        awayPitching = pd.read_html(source, attrs={'id': '%spitching' % teams[0]})
        homePitching = pd.read_html(source, attrs={'id': '%spitching' % teams[1]})

        tables.append(awayBatting)
        tables.append(homeBatting)
        tables.append(awayPitching)
        tables.append(homePitching)

        counter+=1
        print(counter)


getBox()
