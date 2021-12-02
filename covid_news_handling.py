import datetime
import requests

def news_API_request (covid_terms = "Covid COVID-19 coronavirus"):
    url = ('https://newsapi.org/v2/everything?'
       f'q={covid_terms}&'
       f'from={datetime.date}&'
       'sortBy=popularity&'
       'apiKey=d94f92a7e85348be8a233f2740d33a8f')

    response = requests.get(url)
    news_data = response.json()
    news_articles = news_data["articles"]
    #print (news_articles)
    # remove extra unused data
    for article in news_articles:
        #print (article)
        del article["source"]
        del article["author"]
        del article["publishedAt"]
        del article["urlToImage"]
        article["content"] = article["description"]
        del article["description"]
    #print(news_articles)
    return news_articles

#def trim_news()
news_API_request()
    