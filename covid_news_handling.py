import requests
import datetime

def news_API_request (covid_terms = "Covid COVID-19 coronavirus"):
    url = ('https://newsapi.org/v2/everything?'
       f'q={covid_terms}&'
       f'from={datetime.date}&'
       'sortBy=popularity&'
       'apiKey=d94f92a7e85348be8a233f2740d33a8f')

    response = requests.get(url)
    news_data = response.json()
    print (response)
    print (news_data)
    
news_API_request()
    