import json
from json.decoder import JSONDecodeError
import logging
from flask import request
from flask import Flask
from flask import render_template
from werkzeug.utils import redirect
from covid_data_handler import process_covid_data
from covid_data_handler import covid_API_request
from covid_data_handler import get_locations
from covid_news_handling import news_API_request
from covid_news_handling import trim_news
from covid_news_handling import article_remover
from covid_news_handling import url_appender

# import configuration file for logging
# use of eval is a little hacky but I really wanted logging mode to be contained in the config, 
# and this is the best I could come up with
with open ("config.json", "r", encoding = "UTF-8") as config_file:
    configuration = json.load (config_file)
logging.basicConfig(filename='sys.log', encoding='utf-8', level = eval(f'{configuration["logging_mode"]}'))

app = Flask(__name__)

@app.route('/index')
def website_update():
    """Start flask server and get most up to date information, check and act on website queries"""
    remove_article_title = request.args.get('notif')
    update_time = request.args.get('update')
    update_name = request.args.get('two')
    news_toggle = request.args.get('news')
    repeat_toggle = request.args.get('repeat')
    covid_toggle = request.args.get('covid-data')
    remove_update = request.args.get('update_item')

    logging.debug("Data from site:")
    logging.debug("Time for update: %s" % update_time)
    logging.debug("Name of update: %s" % update_name)
    logging.debug("News toggle checked? %s" % news_toggle)
    logging.debug("Repeat toggle checked? %s" % repeat_toggle)
    logging.debug("Data update toggle checked? %s" % covid_toggle)
    logging.debug("Update removed? Name: %s" % remove_update)
    logging.debug("Article to remove: %s" % remove_article_title)

    with open('updates.json', 'r', encoding = "UTF-8") as updates_file:
        try:        
            updates = json.load(updates_file)
            logging.info("Updates loaded")
        except JSONDecodeError:
            updates = []
            logging.warning("Updates file empty; setting empty list")

    if update_name:
        logging.info("Update request found:")
        new_update = {"title" : update_name, "content" : update_time}
        updates.append(new_update)
        logging.info("New update appended to updates.json")
        with open ("updates.json", "w", encoding = "UTF-8") as updates_file:
            json.dump (updates, updates_file, ensure_ascii=False, indent="")
        return redirect ("/index")

    if remove_update:
        logging.info ("Update remove request found:")
        update_count = 0
        for update in updates:
            logging.debug ("Checking update:" + str(update))
            if update["title"] == remove_update:
                logging.info ("Update found; deleting")
                del updates[update_count]
                with open ("updates.json", "w", encoding = "UTF-8") as updates_file:
                    json.dump (updates, updates_file, ensure_ascii=False, indent="")
                return redirect ("/index")
            update_count += 1

    if remove_article_title:
        logging.info ("News remove request found:")
        article_count = 0
        for article in news:
            logging.debug ("Checking for article " + str(article))
            if article["title"] == remove_article_title:
                logging.info ("Article found; deleting from live site and adding to removed-articles.json")
                del news[article_count]
                removed_articles.append(article)
                with open ("removed_articles.json", "w", encoding = "UTF-8") as deleted_articles:
                    json.dump(removed_articles, deleted_articles, ensure_ascii=False, indent="")
                return redirect ("/index")
            article_count += 1

    deaths_total, hospital_cases, national_7day_infections, local_7day_infections = process_covid_data(data_all)
    trimmed_news = trim_news(news)
    national_area_name, local_area_name = get_locations(data_all)
    #logging.info (deaths_total, hospital_cases, national_7day_infections, local_7day_infections)
    return render_template('index.html',
            local_7day_infections = local_7day_infections,
            national_7day_infections = national_7day_infections,
            deaths_total = ("Total deaths: " + str(deaths_total)),
            hospital_cases = ("Current national hospital cases: " + str(hospital_cases)),
            location = local_area_name,
            nation_location = national_area_name,
            news_articles = trimmed_news,
            title = "COVID Dashboard",
            image = "image.jpg",
            updates = updates)

#get removed news from file
with open('removed_articles.json', 'r', encoding = "UTF-8") as removed_articles_file:
    try:        
        removed_articles = json.load(removed_articles_file)
    except JSONDecodeError:
        removed_articles = []
"""
# get updates from file
with open('updates.json', 'r', encoding = "UTF-8") as updates_file:
    try:        
        updates = json.load(updates_file)
        logging.info("Updates loaded")
    except JSONDecodeError:
        pass
        updates = []
        logging.warning("Updates file empty; setting empty list")
"""
data_all = covid_API_request()
news = []
news = article_remover(url_appender(news_API_request()), removed_articles)
# known issue: if all news articles are removed, older ones cannot be pulled
app.run()
