import requests

url = ('https://newsapi.org/v2/everything?sortBy=popularity&apiKey=0020da03e9b44fa1b8396f187c21fd2b&sources=espn')

response = requests.get(url)

print(response.json())
