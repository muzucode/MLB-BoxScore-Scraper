import requests
import re
import pandas as pd
import lxml
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)

def getLeague():

    URL = 'https://www.baseball-reference.com/leagues/MLB/2018-schedule.shtml'
    page = requests.get(URL)
    response = page.text
    extensions = []

    # Create substring of the boxes element
    ss = '&nbsp;&nbsp;&nbsp;&nbsp;<em><a href="/boxes'
    matches = re.finditer(ss, response)
    matches_positions = [match.start() for match in matches]

    numboxes = 0

    # Creates list of box score URL extensions
    for i in range(len(matches_positions)):
        # Iterates until numboxes value breaks loop
        # Each loop adds one boxscore extension to be fetched
        numboxes+=1
        ind = matches_positions[i]
        line= response[ind:ind+66]
        extensions.append(line[38:])
        print('Box score: %s' % i, extensions[i])

        # numTeams determines num of box score requests
        if numboxes == 10:
            break

    return extensions


def getBoxes():
    # Get all URL path extensions for boxscores
    extensions = getLeague()
    masterAwayBatting = []
    masterAwayPitching = []
    masterHomeBatting = []
    masterHomePitching = []
    masterBoxes = []

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
        print('Preparing box scores for: ', teams)

        # Save tables for away/home batting/pitching for individual box score
        awaybatting = pd.read_html(source, attrs = {'id': '%sbatting' % teams[0]})
        homebatting = pd.read_html(source, attrs = {'id': '%sbatting' % teams[1]})
        awaypitching = pd.read_html(source, attrs={'id': '%spitching' % teams[0]})
        homepitching = pd.read_html(source, attrs={'id': '%spitching' % teams[1]})

        # Append individual box scores to masters
        masterAwayBatting.append(awaybatting)
        masterHomeBatting.append(homebatting)
        masterAwayPitching.append(awaypitching)
        masterHomePitching.append(homepitching)

    masterBoxes.append(masterAwayBatting)
    masterBoxes.append(masterHomeBatting)
    masterBoxes.append(masterAwayPitching)
    masterBoxes.append(masterHomePitching)

    return masterBoxes

        # print(teams)


print(getBoxes())
print('Above is a list of all away/home batting/pitching data for the specified number of games')