import logging
import json
from json.decoder import JSONDecodeError
import datetime
import requests
from flask import Markup

# import configuration file for logging
# use of eval is a little hacky but I really wanted logging mode to be contained in the config,
# and this is the best I could come up with
with open ("config.json", "r", encoding = "UTF-8") as config_file:
    configuration = json.load (config_file)
logging.basicConfig(filename='sys.log',
                    encoding='utf-8',
                    level = eval(f'{configuration["logging_mode"]}'))

def news_API_request (covid_terms = "Covid COVID-19 coronavirus"):
    logging.info("News API request acknowledged...")
    logging.info("API key imported as: %s" , configuration["api_key"])
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
        logging.info("Returning news articles")
        return news_articles
    except TimeoutError:
        logging.error("News API request failed - is the News API down?")
    #print (news_articles)

def trim_news(news_articles):
    logging.info ("Trimming display news down to 5 articles...")
    trimmed_news = []
    try:
        for i in range (0,5):
            trimmed_news.append(news_articles[i])
        logging.info ("Trimming complete, returning data")
    except IndexError:
        logging.critical ("News data exhausted; \
            clean removed_articles.json or continue waiting for new news")
    return trimmed_news

def article_remover(news_articles, removed_articles):
    logging.info("Performing startup news deletion...")
    for removed_article_count, current_removed_article in enumerate(removed_articles):
        logging.debug ("Checking for expected deleted article %s" , removed_article_count)
        if current_removed_article in news_articles:
            logging.info ("Article %s match found" , removed_article_count)
            for current_article_count, current_article in enumerate(news_articles):
                if current_removed_article == news_articles[current_article_count]:
                    logging.info ("Deleting matched article %s" , current_article)
                    del news_articles[current_article_count]
                    break
        else:
            logging.error ("Expected article %s was not found to be removed" , \
                removed_article_count)
            logging.error ("Article title: %s" , current_removed_article)
    return news_articles

def url_appender(news_articles):
    """appends relevant URLs to news articles"""
    logging.info ("Appending urls to news content...")
    for current_article in news_articles:
        current_article["content"] = (current_article["content"] + " " + \
            Markup('<a href="'+current_article["url"] +'">'+ "Click for full article..." + "</a>"))
    return news_articles

def update_news():
    with open('removed_articles.json', 'r', encoding = "UTF-8") as removed_articles_file:
        try:
            removed_articles = json.load(removed_articles_file)
            logging.info("Removed articles loaded")
        except JSONDecodeError:
            removed_articles = []
            logging.warning("Removed articles not loaded, is the file empty?")

        # trim_news is not called as trim_news must run every time the website's news
        news = article_remover(\
                url_appender(news_API_request()), removed_articles)
        
        return news