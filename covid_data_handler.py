"""
Module that handles all data, including importing from the Public
Health England API, processing to JSON, saving as file to cache,
parsing the JSON to a CSV-similar file, and finding the values for
the last 7 days' cases, current hospital cases, and total deaths.

Parameters:


Returns:
    [type]: [description]

"""

import json
from uk_covid19 import Cov19API

def parse_csv_data(csv_filename):
    covid_csv_data = []
    data = open(csv_filename, "r", encoding="UTF-8")
    # this next (commented) line is to check if the data has been imported
    # correctly by printing it to console; however, when
    # run, it breaks the appending of the list csv_data
    # current theory: data.read() changes the object type
    # of data to a text wrapper, which has no actionable
    # property "line"
    #print (data.read() +("Raw data from input file"))
    for line in data:
        line = line.strip('\n')
        covid_csv_data.append(line)
    return covid_csv_data


def construct_csv_dictionary(covid_csv_data):
    # setup variables
    list_dict = []
    dictionary_keys = covid_csv_data[0]
    dictionary_keys = dictionary_keys.split(",")
    for line in covid_csv_data:
        if line != covid_csv_data[0]:
            current_line_data = line.split(",")
            #current_line_data = current_line_data.split(",")
            keys_values = list(zip(dictionary_keys, current_line_data))
            current_line_dict = (dict(keys_values))
            list_dict.append(current_line_dict)
    #print (list_dict)
    return (list_dict)


def process_covid_csv_data(covid_csv_data):
    # define base state of variables
    days_summed = 0
    last7days_cases = 0
    csv_dict = construct_csv_dictionary(covid_csv_data)

    # set up latches
    total_deaths_not_assigned = True
    last7days_cases_not_complete = True
    first_date_not_passed = True
    current_hospital_cases_not_assigned = True
    
    # loop through each dictionary of the given data until the return statement is triggered
    for current_line in csv_dict:

        # process data by checking if data is valid to use
        if current_line["cumDailyNsoDeathsByDeathDate"].isnumeric() and total_deaths_not_assigned:
            # this if statement only assigns the first satisfactory value for deaths, as
            # total_deaths is cumulative
            total_deaths = current_line["cumDailyNsoDeathsByDeathDate"]
            print (("Total deaths: ") + total_deaths)

            # switch latch post assignment to prevent reassigning a wrong number in future loops
            total_deaths_not_assigned = False

        if current_line["hospitalCases"].isnumeric() and current_hospital_cases_not_assigned:
            current_hospital_cases = current_line["hospitalCases"]
            # switch latch post assignment to prevent reassigning a wrong number in future loops
            current_hospital_cases_not_assigned = False
            print (("Current hospital cases: ") + current_hospital_cases)

        if current_line["newCasesBySpecimenDate"].isnumeric() and last7days_cases_not_complete:
            if first_date_not_passed:
                # switch latch if the first number (incomplete data) has just been read
                first_date_not_passed = False
                
            else:
                # find new total cases and increment days
                last7days_cases = last7days_cases + int(current_line["newCasesBySpecimenDate"])
                days_summed += 1

                #print (("Current running total for last 7 days cases: ") + str(last7days_cases))
                # switch latch if data summed for the past week
                if days_summed == 7:
                    print (("Last 7 days cases: ") + str(last7days_cases))
                    last7days_cases_not_complete = False

        # check all tasks complete; if so, end function and return variables
        # logic here checks if all 3 values are False ie. have the related variables been assigned
        # checked in order of least likely to complete quickly to most likely to complete quickly
        if not total_deaths_not_assigned and not current_hospital_cases_not_assigned and not last7days_cases_not_complete:
            print ("All tasks in process_covid_csv_data complete")
            return(total_deaths, current_hospital_cases, last7days_cases)

    # function should always complete the earlier check by the end of the given csv
    # - if not, the for loop ends and this line will be printed
    print ("Error: not all functions in process_covid_csv_data completed")


def covid_API_request (location = "Exeter", location_type = "ltla"):
    # set variables for API query
    england_only = ['areaType=nation','areaName=England']
    # setup requested metrics from API
    cases_and_deaths = {
        "areaCode": "areaCode",
        "date": "date",
        "cumDeathsByDeathDate" : "cumDeathsByDeathDate",
        "hospitalCases" : "hospitalCases",
        "newCasesBySpecimenDate" : "newCasesBySpecimenDate",
    }
    # query API using imported function at beginning of code
    api = Cov19API(filters=england_only, structure=cases_and_deaths)
    all_data = api.get_json()
    # all_data is the entire API request; data is the useful parts of that
    data = all_data["data"]
    #print (type(data))
    #print (data)
    # prepare and send all_data to be cached in json
    export_file = open('current_data.json', 'w', encoding="UTF-8")
    json.dump(data, export_file, indent = "")
    return (all_data)

# run functions with given local copy of test data
csv_data = parse_csv_data("nation_2021-10-28.csv")
deaths, hospital_cases, last_week_cases = process_covid_csv_data(csv_data)
covid_API_request (None, None)
construct_csv_dictionary(parse_csv_data("nation_2021-10-28.csv"))