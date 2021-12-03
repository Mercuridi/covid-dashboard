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

def trim_news(news_articles, removed_articles, ):
    print ("Trimming news: ")
    print ("Checking for removed articles...")
    for article_count in range(len(removed_articles)):
        print ("Checking for deleted article " + str(article_count))
        if removed_articles[article_count] in news_articles:
            print ("Article match found; deleting...")
            for i in range(len(news_articles)):
                if removed_articles[article_count] == news_articles[i]:
                    del news_articles[i]
                    break
        else:
            print ("No articles found to be removed")
    print ("Trimming returned news down to 5 articles...")
    trimmed_news = []
    for i in range (0,5):
        trimmed_news.append(news_articles[i])
    print ("Trimming complete")
    return trimmed_news


news_API_request()
    