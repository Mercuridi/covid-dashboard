"""Handles COVID data processing and importing

Module that handles all data, including importing from the Public
Health England API, processing to JSON, saving as files,
parsing the JSON so it is usable in the written code, and finding the values for
the last 7 days' cases, current hospital cases, and total deaths.
"""

import json
from uk_covid19 import Cov19API

def parse_csv_data(csv_filename):
    """Method to open CSV files and return the data as a list of lists"""
    covid_csv_data = []
    data = open(csv_filename, "r", encoding="UTF-8")
    for line in data:
        line = line.strip('\n')
        covid_csv_data.append(line)
    return covid_csv_data
def construct_csv_dictionary(covid_csv_data):
    """
    Method to convert a list of lists to a dictionary with
    proper keys, given that the CSV file is formatted correctly
    """
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
    """Method to import a parsed CSV file and return relevant data"""
    # define base state of variables
    days_summed = 0
    last7days_cases = 0
    csv_dict = construct_csv_dictionary(covid_csv_data)

    # set up latches
    total_deaths_assigned = False
    last7days_cases_complete = False
    first_date_passed = False
    current_hospital_cases_assigned = False

    # loop through each dictionary of the given data until the return statement is triggered
    for current_line in csv_dict:

        # process data by checking if data is valid to use
        if current_line["cumDailyNsoDeathsByDeathDate"].isnumeric() and not total_deaths_assigned:
            # this if statement only assigns the first satisfactory value for deaths, as
            # total_deaths is cumulative
            total_deaths = current_line["cumDailyNsoDeathsByDeathDate"]
            print (("Total deaths: ") + total_deaths)

            # switch latch post assignment to prevent reassigning a wrong number in future loops
            total_deaths_assigned = True

        if current_line["hospitalCases"].isnumeric() and not current_hospital_cases_assigned:
            current_hospital_cases = current_line["hospitalCases"]
            # switch latch post assignment to prevent reassigning a wrong number in future loops
            current_hospital_cases_assigned = True
            print (("Current hospital cases: ") + current_hospital_cases)

        if current_line["newCasesBySpecimenDate"].isnumeric() and not last7days_cases_complete:
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
                    last7days_cases_complete = True

        # check all tasks complete; if so, end function and return variables
        # logic here checks if all 3 values are False ie. have the related variables been assigned
        # checked in order of least likely to complete quickly to most likely to complete quickly
        if total_deaths_assigned and current_hospital_cases_assigned and last7days_cases_complete:
            print ("All tasks in process_covid_csv_data complete")
            return(total_deaths, current_hospital_cases, last7days_cases)

    # function should always complete the earlier check by the end of the given csv
    # if not, the for loop ends and this line will be printed
    print ("Error: not all functions in process_covid_csv_data completed")
def dictionary_combiner (local_data, national_data):
    """Combines a pair of dictionaries into one so all data can be stored in one file"""
    # for each dictionary in the list:
    for i in (range(len(local_data))):
        # rename national key
        national_data[i-1]["national_newCasesBySpecimenDate"] = national_data[i-1]["newCasesBySpecimenDate"]
        # add local infection data
        national_data[i-1].update(local_data[i-1])
        # rename local key
        national_data[i-1]["local_newCasesBySpecimenDate"] = national_data[i-1]["newCasesBySpecimenDate"]
        # clean up bad data
        del national_data[i-1]["newCasesBySpecimenDate"]
    return national_data
def covid_API_request (location = "Exeter", location_type = "ltla"):
    """Polls the public COVID API to request data and stores it in a pair of files.

    Args:
        location (str, optional): location within nation. Defaults to "Exeter".
        location_type (str, optional): type of location. Defaults to "ltla".

    Returns:
        dictionary data_all: compiled data of every request as a single dictionary

    Files:
        writes to files data_all.json, data_local.json, data_national.json
    """
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
    #print (data_local, data_national)
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
    # return all data
    return data_all
def parse_json_data(json_filename = "data_all.json"):
    """Method to  open a json file and return it as a dictionary

    Args:
        json_filename (str, optional): filename of json to open. Defaults to "data_all.json".

    Returns:
        dictionary: contents of json file
    """
    with open(json_filename, "r", encoding ="UTF-8") as file:
        covid_json_data = json.load(file)
    #print (covid_json_data)
    return covid_json_data
def process_covid_json_data(covid_json_data):
    """Method to take a dictionary of COVID data and return all relevant information

    Dependant on keynames assigned in other functions in this module
    """
    # define base state of variables
    national_days_summed = 0
    local_days_summed = 0
    national_last7days_cases = 0
    local_last7days_cases = 0

    # set up latches
    total_deaths_assigned = False
    national_last7days_cases_assigned = False
    local_last7days_cases_assigned = False
    national_first_date_passed = False
    local_first_date_passed = False
    current_hospital_cases_assigned = False

    # loop through each dictionary of the given data until the return statement is triggered
    for current_line in covid_json_data:
        # make sure all expected keynames are present
        if len(current_line) == 7:
            #print (current_line)
            # process data by checking if data is valid to use
            if current_line["cumDailyNsoDeathsByDeathDate"] is not None and not total_deaths_assigned:
                # this if statement only assigns the first satisfactory value for deaths, as
                # total_deaths is cumulative
                total_deaths = current_line["cumDailyNsoDeathsByDeathDate"]
                # switch latch post assignment to prevent reassigning a wrong number in future loops
                total_deaths_assigned = True
            if current_line["hospitalCases"] is not None and not current_hospital_cases_assigned:
                current_hospital_cases = current_line["hospitalCases"]
                # switch latch post assignment to prevent reassigning a wrong number in future loops
                current_hospital_cases_assigned = True
            if current_line["national_newCasesBySpecimenDate"] is not None and not national_last7days_cases_assigned:
                if not national_first_date_passed:
                    # switch latch if the first number (incomplete data) has just been read
                    national_first_date_passed = True
                else:
                    # find new total cases and increment days
                    national_last7days_cases = national_last7days_cases + current_line["national_newCasesBySpecimenDate"]
                    national_days_summed += 1
                    #print (("Current running total for last 7 days cases: ") + str(last7days_cases))
                    # switch latch if data summed for the past week
                    if national_days_summed == 7:
                        national_last7days_cases_assigned = True
            if current_line["local_newCasesBySpecimenDate"] is not None and not local_last7days_cases_assigned:
                if not local_first_date_passed:
                    # switch latch if the first number (incomplete data) has just been read
                    local_first_date_passed = True
                else:
                    # find new total cases and increment days
                    local_last7days_cases = local_last7days_cases + current_line["local_newCasesBySpecimenDate"]
                    local_days_summed += 1
                    # switch latch if data summed for the past week
                    if local_days_summed == 7:
                        local_last7days_cases_assigned = True

        # check all tasks complete; if so, end function and return variables
        # logic here checks if all 4 values are True ie. have the related variables been assigned
        if total_deaths_assigned and current_hospital_cases_assigned and national_last7days_cases_assigned and local_last7days_cases_assigned:
            #print ("All tasks in process_covid_json_data complete")
            #print (("Local last 7 days cases: ") + str(local_last7days_cases))
            #print (("National last 7 days cases: ") + str(national_last7days_cases))
            #print (("Current hospital cases: ") + str(current_hospital_cases))
            #print (("Total deaths: ") + str(total_deaths))
            #print ("Data returned")
            return (total_deaths, current_hospital_cases, national_last7days_cases, local_last7days_cases)

    # function should always complete the earlier check by the end of the given json
    # if not, the for loop ends and this line will be printed
    print ("Error: not all functions in process_covid_json_data completed")
def get_covid_data_json():
    """Function to call all json functions to get up-to-date COVID data

    Returns:
        int: all useful COVID data for display in dashboard
        deaths, hospital_cases, national_last_week_cases, local_last_week_cases
    """
    covid_API_request ()
    deaths, hospital_cases, national_last_week_cases, local_last_week_cases = process_covid_json_data (parse_json_data())
    return deaths, hospital_cases, national_last_week_cases, local_last_week_cases

# run functions with local test data for CSV
#process_covid_csv_data (parse_csv_data ("nation_2021-10-28.csv"))
# run all functions to update data_all.json
get_covid_data_json()
