from flask import Flask
from flask import render_template
from flask import request
from covid_data_handler import *

app = Flask(__name__)

@app.route("/index")
def website_update():
    covid_API_request ()
    deaths_total, hospital_cases, national_7day_infections = process_covid_json_data (parse_json_data("data_national.json"))
    local_7day_infections = process_covid_json_data (parse_json_data("data_local.json"))
    print (deaths_total, hospital_cases, national_7day_infections, local_7day_infections)
    return render_template("index.html")
#local_7day_infections = local_7day_infections, national_7day_infections = national_7day_infections, deaths_total = deaths_total, hospital_cases = hospital_cases)
if __name__ == '__main__':
    app.run()