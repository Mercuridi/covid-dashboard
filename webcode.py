from flask import Flask
from flask import render_template
from flask import request
from covid_data_handler import process_covid_json_data
from covid_data_handler import parse_json_data
from covid_data_handler import covid_API_request
from covid_data_handler import get_covid_data_json
from covid_data_handler import get_locations

app = Flask(__name__)

@app.route('/index')
def website_update():
    covid_API_request ()
    deaths_total, hospital_cases, national_7day_infections, local_7day_infections = get_covid_data_json()
    national_areaType, national_areaName, local_areaType, local_areaName = get_locations(parse_json_data())
    print (deaths_total, hospital_cases, national_7day_infections, local_7day_infections)
    return render_template('index.html',
            local_7day_infections = local_7day_infections, national_7day_infections = national_7day_infections,
            deaths_total = ("Total deaths: " + str(deaths_total)), hospital_cases = ("Current national hospital cases: " + str(hospital_cases)),
            location = local_areaName, nation_location = national_areaName)

app.run()
