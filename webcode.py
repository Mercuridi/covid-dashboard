import json
from json.decoder import JSONDecodeError
import logging
import flask
from flask import request
from flask import Flask, render_template
from werkzeug.utils import redirect
from covid_data_handler import process_covid_data
from covid_data_handler import covid_API_request
from covid_data_handler import get_locations
from covid_news_handling import news_API_request
from covid_news_handling import trim_news

logging.basicConfig(filename='sys.log', encoding='utf-8', level = logging.INFO, filemode = "a")

app = Flask(__name__)

@app.route('/index')
def website_update():
    """Start flask server and get most up to date information, check for website queries"""
    remove_article_title = request.args.get('notif')
    update_time = request.args.get('update')
    update_name = request.args.get('two')
    news_toggle = request.args.get('news')
    repeat_toggle = request.args.get('repeat')
    covid_toggle = request.args.get('covid-data')
    remove_update = request.args.get('update_item')
    logging.info("Data from site:")
    logging.info("Time for update: " + str(update_time))
    logging.info("Name of update: " + str(update_name))
    logging.info("News toggle checked? " + str(news_toggle))
    logging.info("Repeat toggle checked? " + str(repeat_toggle))
    logging.info("Data update toggle checked? " + str(covid_toggle))
    logging.info("Update removed? Name: " + str(remove_update))
    logging.info("Article to remove: " + str(remove_article_title))
    if update_name:
        logging.info("Update request found:")
        new_update = {"title" : update_name, "content" : update_time}
        updates.append(new_update)
        logging.info(updates)
        with open ("updates.json", "w", encoding = "UTF-8") as updates_file:
            json.dump (str(updates), updates_file, ensure_ascii=False, indent="")
        return redirect ("/index")
    if remove_update:
        logging.info ("Update remove request found:")
        update_count = 0
        for update in updates:
            logging.info ("Checking update:" + str(update))
            if update["title"] == remove_update:
                logging.info ("Update found; deleting")
                del updates[update_count]
                with open ("updates.json", "w", encoding = "UTF-8") as updates_file:
                    json.dump (str(updates), updates_file, ensure_ascii=False, indent="")
                return redirect ("/index")
            update_count += 1
    if remove_article_title:
        logging.info ("News remove request found:")
        article_count = 0
        for article in news:
            logging.info ("Checking for article " + str(article))
            if article["title"] == remove_article_title:
                logging.info ("Article found; deleting")
                del news[article_count]
                removed_articles.append(article)
                with open ("removed_articles.json", "w", encoding = "UTF-8") as deleted_articles:
                    json.dump(removed_articles, deleted_articles, ensure_ascii=False, indent="")
                return redirect ("/index")
            article_count += 1
    deaths_total, hospital_cases, national_7day_infections, local_7day_infections = process_covid_data(data_all)
    trimmed_news = trim_news(news, removed_articles)
    national_areaType, national_areaName, local_areaType, local_areaName = get_locations(data_all)
    #logging.info (deaths_total, hospital_cases, national_7day_infections, local_7day_infections)
    return render_template('index.html',
            local_7day_infections = local_7day_infections,
            national_7day_infections = national_7day_infections,
            deaths_total = ("Total deaths: " + str(deaths_total)),
            hospital_cases = ("Current national hospital cases: " + str(hospital_cases)),
            location = local_areaName,
            nation_location = national_areaName,
            news_articles = trimmed_news,
            title = "COVID Dashboard",
            image = "image.jpg",
            updates = updates)


news = []
with open('removed_articles.json', 'r', encoding = "UTF-8") as removed_articles_file:
    try:        
        removed_articles = json.load(removed_articles_file)
    except JSONDecodeError:
        pass
        removed_articles = []
with open('updates.json', 'r', encoding = "UTF-8") as updates_file:
    try:        
        updates = json.load(updates_file)
    except JSONDecodeError:
        pass
        updates = []

data_all = covid_API_request()
news = news_API_request()
# known issue: if all news articles are removed, older ones cannot be pulled
app.run()
