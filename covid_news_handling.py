import datetime
from flask import config
import requests
import logging
import json

#import configuration file for logging
with open ("config.json", "r", encoding = "UTF-8") as config_file:
    configuration = json.load (config_file)
logging.basicConfig(filename='sys.log', encoding='utf-8', level = eval(f'{configuration["logging_mode"]}'))

def news_API_request (covid_terms = "Covid COVID-19 coronavirus"):
    logging.info("News API request acknowledged...")
    logging.info("API key imported as: " + configuration["api_key"])
    url = (
        'https://newsapi.org/v2/everything?'
       f'q={covid_terms}&'
       f'from={datetime.date}&'
        'sortBy=popularity&'
       f'apiKey={configuration["api_key"]}'
       )
    try:
        response = requests.get(url)
        news_data = response.json()
        news_articles = news_data["articles"]
        # remove extra unused data
        logging.info("Deleting extra information from NewsAPI request...")
        for article in news_articles:
            #print (article)
            del article["source"]
            del article["author"]
            del article["publishedAt"]
            del article["urlToImage"]
            article["content"] = article["description"]
            del article["description"]
        #print(news_articles)
        logging.info("Returning news articles")
        return news_articles
    except:
        pass
        logging.error("News API request failed - is the News API down?")
    #print (news_articles)

def trim_news(news_articles, removed_articles, ):
    logging.info ("Trimming news: ")
    logging.info ("Checking for removed articles...")
    for article_count in range(len(removed_articles)):
        logging.debug ("Checking for deleted article " + str(article_count))
        if removed_articles[article_count] in news_articles:
            logging.info ("Article match found; deleting...")
            for i in range(len(news_articles)):
                if removed_articles[article_count] == news_articles[i]:
                    del news_articles[i]
                    break
        else:
            logging.info ("No articles found to be removed")
    logging.info ("Trimming returned news down to 5 articles...")
    trimmed_news = []
    for i in range (0,5):
        trimmed_news.append(news_articles[i])
    logging.info ("Trimming complete")
    return trimmed_news