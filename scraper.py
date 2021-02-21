import requests

URL = 'https://www.baseball-reference.com/leagues/MLB/2018-schedule.shtml'
page = requests.get(URL)
response = page.text

file = open('test.html', 'w')
file.write(response)
file.close()

print(response)