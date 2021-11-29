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
    for line in data:
        line = line.strip('\n')
        covid_csv_data.append(line)
    return covid_csv_data


def construct_csv_dictionary(covid_csv_data):
    # setup variables
    list_dict = []
    dictionary_keys = covid_csv_data[0]
    dictionary_keys = dictionary_keys.split(",")
    # iterate over each line to construct list of dictionaries
    for line in covid_csv_data:
        # skip first line which should contain keys
        if line != covid_csv_data[0]:
            # split line data into list of strings
            current_line_data = line.split(",")
            keys_values = list(zip(dictionary_keys, current_line_data))
            # create dictionaries
            current_line_dict = (dict(keys_values))
            # add each dictionary to a list
            list_dict.append(current_line_dict)
    #print (list_dict)
    return list_dict


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
    # if not, the for loop ends and this line will be printed
    print ("Error: not all functions in process_covid_csv_data completed")

def dictionary_combiner (local_data, national_data):
    # combine the 2 dictionaries returned from the separate requests
    # into a single "master dictionary"
    for i in (range(len(local_data))):
        national_data[i-1].update(local_data[i-1])
    all_data = national_data
    return all_data

def covid_API_request (location = "Exeter", location_type = "ltla"):
    # set variable for API queries
    location_info_local =       [
                        f'areaType={location_type}',
                        f'areaName={location}'
                            ]
    location_info_national = [
                    'areaType=nation',
                    'areaName=England'
                        ]
    # setup requested metrics from API
    national_request = {
        "areaType": "areaType",
        "areaName": "areaName",
        "date": "date",
        "cumDailyNsoDeathsByDeathDate" : "cumDailyNsoDeathsByDeathDate",
        "hospitalCases" : "hospitalCases",
        "newCasesBySpecimenDate" : "newCasesBySpecimenDate",
    }

    local_request = {
        "newCasesBySpecimenDate" : "newCasesBySpecimenDate",
    }

    # query API using imported Cov19API function at beginning of code
    api1 = Cov19API (filters = location_info_national, structure = national_request)
    api2 = Cov19API (filters = location_info_local, structure = local_request)
    query_1 = api1.get_json()
    query_2 = api2.get_json()
    # api1, api2 is the entire API request; data1, data2 is the useful parts of them
    data_national = query_1["data"]
    data_local = query_2["data"]
    #print (data1, data2)
    # prepare and send useful data to be cached in json - 2 files
    # Commented out as 2 exports is unnecessary with the later method,
    # but keeping the code may be useful for debugging in the future
    export_file = open('data_national.json', 'w', encoding="UTF-8")
    json.dump(data_national, export_file, indent = "")
    export_file = open('data_local.json', 'w', encoding="UTF-8")
    json.dump(data_local, export_file, indent = "")

    data_all = dictionary_combiner(data_local, data_national)

    # export master dictionary to json file
    export_file = open('data_all.json', 'w', encoding="UTF-8")
    json.dump(data_all, export_file, indent = "")

    return data_all

def parse_json_data(json_filename = "data_national.json"):
    with open(json_filename, "r", encoding ="UTF-8") as file:
        covid_json_data = json.load(file)
    #print (covid_json_data)
    return covid_json_data

def process_covid_json_data(covid_json_data):
    # define base state of variables
    days_summed = 0
    last7days_cases = 0

    # set up latches
    total_deaths_assigned = False
    last7days_cases_assigned = False
    first_date_passed = False
    current_hospital_cases_assigned = False

    # loop through each dictionary of the given data until the return statement is triggered
    for current_line in covid_json_data:
        # national data dictionary has more keys than local data: if this code is run on
        # local data the program crashes
        if len(current_line) > 1:
            # process data by checking if data is valid to use
            if current_line["cumDailyNsoDeathsByDeathDate"] is not None and not total_deaths_assigned:
                # this if statement only assigns the first satisfactory value for deaths, as
                # total_deaths is cumulative
                total_deaths = current_line["cumDailyNsoDeathsByDeathDate"]
                # switch latch post assignment to prevent reassigning a wrong number in future loops
                total_deaths_assigned = True
                print (("Total deaths: ") + str(total_deaths))
            if current_line["hospitalCases"] is not None and not current_hospital_cases_assigned:
                current_hospital_cases = current_line["hospitalCases"]
                # switch latch post assignment to prevent reassigning a wrong number in future loops
                current_hospital_cases_assigned = True
                print (("Current hospital cases: ") + str(current_hospital_cases))
        # this code is run on local and national data1
        if current_line["newCasesBySpecimenDate"] is not None and not last7days_cases_assigned:
            if not first_date_passed:
                # switch latch if the first number (incomplete data) has just been read
                first_date_passed = True
            else:
                # find new total cases and increment days
                last7days_cases = last7days_cases + int(current_line["newCasesBySpecimenDate"])
                days_summed += 1

                #print (("Current running total for last 7 days cases: ") + str(last7days_cases))
                # switch latch if data summed for the past week
                if days_summed == 7:
                    print (("Last 7 days cases: ") + str(last7days_cases))
                    last7days_cases_assigned = True

        # check all tasks complete; if so, end function and return variables
        # logic here checks if all 3 values are False ie. have the related variables been assigned
        # checked in order of least likely to complete quickly to most likely to complete quickly
        if total_deaths_assigned and current_hospital_cases_assigned and last7days_cases_assigned:
            print ("All tasks in process_covid_json_data complete")
            return(total_deaths, current_hospital_cases, last7days_cases)
        if len(current_line) == 1 and last7days_cases_assigned:
            print ("Only local data detected: returning local 7 days infections")
            return last7days_cases

    # function should always complete the earlier check by the end of the given json
    # if not, the for loop ends and this line will be printed
    print ("Error: not all functions in process_covid_json_data completed")

# run functions with local test data for CSV, live API call for JSON
#csv_data = parse_csv_data ("nation_2021-10-28.csv")
#construct_csv_dictionary (parse_csv_data("nation_2021-10-28.csv"))
#process_covid_csv_data (csv_data)
covid_API_request ()
national_json_data = parse_json_data("data_national.json")
local_json_data = parse_json_data("data_local.json")
deaths, hospital_cases, national_last_week_cases = process_covid_json_data (national_json_data)
local_last_week_cases = process_covid_json_data (local_json_data)
