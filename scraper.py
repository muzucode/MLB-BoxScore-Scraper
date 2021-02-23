import requests
import re
import pandas as pd
from datetime import datetime, timedelta
import lxml
pd.set_option('display.max_columns', 4)
pd.set_option('display.max_row', 2)
pd.set_option('display.width', 1000)


def getLeague(amtRequested, season):
    # Initial HTML request
    URL = 'https://www.baseball-reference.com/leagues/MLB/%s-schedule.shtml' % season
    page = requests.get(URL)
    response = page.text
    extensions = []
    gamedates = []
    # Game codes designate if game is in a double header or not
    gamecodes = []
    gameid = []
    fullurls = []


    # Create substring of the boxes element
    ss = '&nbsp;&nbsp;&nbsp;&nbsp;<em><a href="/boxes'
    matches = re.finditer(ss, response)
    matches_positions = [match.start() for match in matches]

    numboxes = 0

    # Creates list of box score URL extensions and corresponding guide cols
    for i in range(len(matches_positions)):
        # Iterates until numboxes value breaks loop
        # Each loop adds one boxscore extension to be fetched
        numboxes+=1
        ind = matches_positions[i]
        line= response[ind:ind+66]
        extensions.append(line[38:])
        gamedates.append(extensions[i][-15:-7])
        gamecodes.append(extensions[i][-7:-6])
        id_string = extensions[i][-15:-7] + str(numboxes)
        gameid.append(id_string)
        fullurls.append('https://www.baseball-reference.com/' + extensions[i])
        # Guidance Columns
        print('Box score: %s' % i, extensions[i], ' || Date: ', gamedates[i], ' || Game code: ', gamecodes[i], ' || Game ID: ', gameid[i], ' || ', fullurls[i]  )
        # If amtRequested is 999, loop will mine every box score from the season
        if amtRequested != 999:
            if numboxes == amtRequested:
                break

    # Cols to be appended on to the final DFs for guidance/indexing purposes when analyzing
    guidecols = [gamedates, gamecodes, gameid, fullurls]
    return [extensions, guidecols]


def getBoxes(amtRequested, season):
    # Get all URL path extensions for boxscores
    extensions, guidecols = getLeague(amtRequested, season)
    # Get all corresponding guidance columns for each extension
    masterAwayBatting = []
    masterAwayPitching = []
    masterHomeBatting = []
    masterHomePitching = []
    masterBoxes = []

    # If user inputs 999 games, change to # of box scores found
    if amtRequested == 999:
        amtRequested = len(extensions)

    # Cycle through all the extensions passed over
    for i in range(len(extensions)):
        URL = 'https://www.baseball-reference.com/%s' % extensions[i]
        source = requests.get(URL)

        # Remove the comment markers (tables are commented on get request)
        source = source.text
        source = source.replace("<!--", "")
        source = source.replace("-->", "")

        # Get away and home team names for dynamic design
        def getTeams():
            # Search for <title> tag to dynamically assign team variables
            ss1 = '<title>'
            ss2 = '</title>'
            matches1 = re.finditer(ss1, source)
            matches_positions1 = [match.start() for match in matches1]
            matches2 = re.finditer(ss2, source)
            matches_positions2 = [match.start() for match in matches2]

            # Set two indexes equal to start/end of <title> tag
            ind1 = matches_positions1[0]
            ind2 = matches_positions2[0]

            # X = entire title code
            x = source[ind1 + 7:ind2]
            # Clean up title code for indexing
            x = x.replace(' ', '')
            x = x.replace('.', '')
            # Find all iterations of 'at'
            matches3 = re.finditer('at', x)
            matches_positions3 = [match.start() for match in matches3]


            # If there is 1 'at', just replace with @
            if len(matches_positions3) == 1:
                x = x.replace('at', '@')
            else:
                # If there are 2+ 'at', cycle through and replace by index
                for r in range(len(matches_positions3)):
                    # If the character to the right of 'at' is uppercase, then reformat the string
                    if x[matches_positions3[r]+2].isupper():
                        # print('Successfully replaced --at-- with --@--')
                        atInd = matches_positions3[r]
                        x = x[:atInd]+'@'+ x[atInd+2:]
                        # Break statement to leave 'at' instance cycling
                        # Once an 'at' meets this condition, then the problem is solved
                        break
                    # STAEMENT BELOW IS FOR DEBUGGING ONLY
                    # else:
                    #     print('--at-- #',r+1,' of ',len(matches_positions3), ' was skipped over for --at-- to --@-- replacement due to being in a team name.')

            # Get index of '@' and 'BoxScore' for team name slicing
            y = x.index('@')
            z = x.index('BoxScore')
            awayTeam = x[0:y]
            homeTeam = x[y + 1:z]

            return [awayTeam, homeTeam]


        # Assign teams with getTeams()
        teams = getTeams()
        print('Preparing box score # %s for: ' % i, teams)

        # Save dataframes for away/home batting/pitching for individual box score
        awaybatting = pd.read_html(source, attrs = {'id': '%sbatting' % teams[0]}, header= 0)
        homebatting = pd.read_html(source, attrs = {'id': '%sbatting' % teams[1]}, header= 0)
        awaypitching = pd.read_html(source, attrs={'id': '%spitching' % teams[0]}, header= 0)
        homepitching = pd.read_html(source, attrs={'id': '%spitching' % teams[1]}, header= 0)

        # Add Guidance Columns to each dataframe
        # Each of these are a LIST OF DATAFRAMES, MUST BE INDEXED!
        counter = 0
        for a_list in [awaybatting, homebatting, awaypitching, homepitching]:

            if counter % 2 == 0:
                a_list[0]['HomeAway'] = 'Away'
            else:
                a_list[0]['HomeAway'] = 'Home'

            if counter == 0 or counter == 1:
                a_list[0]['BattingPitching'] = 'Batting'
            else:
                a_list[0]['BattingPitching'] = 'Pitching'


            a_list[0]['Date'] = guidecols[0][i]
            a_list[0]['Code'] = guidecols[1][i]
            a_list[0]['ID'] = guidecols[2][i]
            a_list[0]['Full URL'] = guidecols[3][i]

            counter+=1

        # Append individual box scores to masters
        masterAwayBatting.append(awaybatting)
        masterHomeBatting.append(homebatting)
        masterAwayPitching.append(awaypitching)
        masterHomePitching.append(homepitching)

    finalAwayBatting  = pd.DataFrame()
    finalHomeBatting  = pd.DataFrame()
    finalAwayPitching = pd.DataFrame()
    finalHomePitching = pd.DataFrame()
    for v in range(amtRequested):
        finalAwayBatting = pd.concat([finalAwayBatting,masterAwayBatting[v][0]])
        finalHomeBatting = pd.concat([finalHomeBatting,masterHomeBatting[v][0]])
        finalAwayPitching = pd.concat([finalAwayPitching,masterAwayPitching[v][0]])
        finalHomePitching = pd.concat([finalHomePitching,masterHomePitching[v][0]])


    # Remove all the 'Team Totals' rows since I don't need them
    finalAwayBatting = finalAwayBatting[finalAwayBatting['Batting'] != 'Team Totals']
    finalHomeBatting = finalHomeBatting[finalHomeBatting['Batting'] != 'Team Totals']
    finalAwayPitching = finalAwayPitching[finalAwayPitching['Pitching'] != 'Team Totals']
    finalHomePitching = finalHomePitching[finalHomePitching['Pitching'] != 'Team Totals']

    # Group all the final DFs together for return
    masterBoxes = [
        finalAwayBatting,
        finalHomeBatting,
        finalAwayPitching,
        finalHomePitching
    ]

    # Write to CSVs
    finalAwayBatting.to_csv('AwayBatting%s.csv' % season, sep=',')
    finalHomeBatting.to_csv('HomeBatting%s.csv' % season, sep=',')
    finalAwayPitching.to_csv('AwayPitching%s.csv' % season, sep=',')
    finalHomePitching.to_csv('HomePitching%s.csv' % season, sep=',')

    return masterBoxes




# First parameter of 999 will give you entire season
print(getBoxes(300,'2015'))
print('Above is a list of all away/home batting/pitching data for the specified number of games')
