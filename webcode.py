import logging
from flask import Flask
from flask import render_template
from flask import request
from covid_data_handler import process_covid_data
from covid_data_handler import covid_API_request
from covid_data_handler import get_covid_data
from covid_data_handler import get_locations
from covid_news_handling import news_API_request

logging.basicConfig(filename='sys.log', encoding='utf-8')

app = Flask(__name__)
news = []
updates = []

@app.route('/index')
def website_update():
    """Start flask server and get most up to date information"""
    #news = news_API_request()
    remove_article = request.args.get('notif')
    update_time = request.args.get('update')
    update_name = request.args.get('two')
    if update_time:
        print('checkpoint')
        #set scheduled update
    if remove_article:
        print('checkpoint')
        #remove relevant article

    deaths_total, hospital_cases, \
        national_7day_infections, local_7day_infections = process_covid_data(data_all)

    national_areaType, national_areaName, local_areaType, local_areaName = get_locations(data_all)
    #print (deaths_total, hospital_cases, national_7day_infections, local_7day_infections)
    return render_template('index.html',
            local_7day_infections = local_7day_infections, national_7day_infections = national_7day_infections,
            deaths_total = ("Total deaths: " + str(deaths_total)), hospital_cases = ("Current national hospital cases: " + str(hospital_cases)),
            location = local_areaName, nation_location = national_areaName, news_articles = news, title = "COVID Dashboard", image = "image.jpg")

#def form_submission():
    
#print(news_API_request())
data_all = covid_API_request()
news = news_API_request()
app.run()
