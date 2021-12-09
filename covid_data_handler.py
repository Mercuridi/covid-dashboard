"""Handles COVID data processing and importing

Module that handles all data, including importing from the Public
Health England API and finding the values for
the last 7 days' cases, current hospital cases, and total deaths.
"""
import json
from json.decoder import JSONDecodeError
import sched
import time
import logging
from uk_covid19 import Cov19API
from werkzeug.utils import redirect
from covid_news_handling import update_news

flask_update = sched.scheduler(timefunc = time.time, delayfunc = time.sleep)

# import configuration file for logging
# use of eval is a little hacky but I really wanted logging mode to be contained in the config,
# and this is the best I could come up with
with open ("config.json", "r", encoding = "UTF-8") as config_file:
    configuration = json.load (config_file)
logging.basicConfig(filename='sys.log',
                    encoding='utf-8',
                    level = eval(f'{configuration["logging_mode"]}'))

# CONVERT MODULE TO USE LOCATION FROM CONFIG

def parse_csv_data(csv_filename):
    """Method to open CSV files and return the data as a list of lists"""
    covid_csv_data = []
    data = open(csv_filename, "r", encoding="UTF-8")
    for line in data:
        line = line.strip('\n')
        covid_csv_data.append(line)
    data.close()
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
            logging.info ("Total deaths: %d", total_deaths)

            # switch latch post assignment to prevent reassigning a wrong number in future loops
            total_deaths_assigned = True

        if current_line["hospitalCases"].isnumeric() and not current_hospital_cases_assigned:
            current_hospital_cases = current_line["hospitalCases"]
            # switch latch post assignment to prevent reassigning a wrong number in future loops
            current_hospital_cases_assigned = True
            logging.info ("Current hospital cases: %d", current_hospital_cases)

        if current_line["newCasesBySpecimenDate"].isnumeric() and not last7days_cases_complete:
            if not first_date_passed:
                # switch latch if the first number (incomplete data) has just been read
                first_date_passed = True

            else:
                # find new total cases and increment days
                last7days_cases = last7days_cases + int(current_line["newCasesBySpecimenDate"])
                days_summed += 1

                logging.debug \
                    ("Current running total for last 7 days cases: %d" , last7days_cases)
                # switch latch if data summed for the past week
                if days_summed == 7:
                    logging.info ("Last 7 days cases: %d" , last7days_cases)
                    last7days_cases_complete = True

        # check all tasks complete; if so, end function and return variables
        # logic here checks if all 3 values are False ie. have the related variables been assigned
        # checked in order of least likely to complete quickly to most likely to complete quickly
        if total_deaths_assigned and current_hospital_cases_assigned and last7days_cases_complete:
            logging.info ("All tasks in process_covid_csv_data complete")
            return(total_deaths, current_hospital_cases, last7days_cases)

    # function should always complete the earlier check by the end of the given csv
    # if not, the for loop ends and this line will be printed
    logging.warning("Error: not all functions in process_covid_csv_data completed")


def get_locations (covid_data):
    """find location/nation from API request

    Args:
        json_filename (str, optional): variable to read data from.
    Returns:
        national_areaType, national_areaName, local_areaType, local_areaName (str)
    """
    #national_area_type = covid_data[0]["national_areaType"]
    national_area_name = covid_data[0]["national_areaName"]
    #local_area_type = covid_data[0]["local_areaType"]
    local_area_name = covid_data[0]["local_areaName"]
    return national_area_name, local_area_name


def dictionary_combiner (local_data, national_data):
    """Combines a pair of dictionaries into one so all data can be stored in one variable"""
    # for each dictionary in the list:
    for i in (range(len(local_data))):
        # combine last 7 days deaths data into one file
        # rename national keys
        national_data[i-1]["national_newCasesBySpecimenDate"] = \
            national_data[i-1]["newCasesBySpecimenDate"]
        national_data[i-1]["national_areaType"] = national_data[i-1]["areaType"]
        national_data[i-1]["national_areaName"] = national_data[i-1]["areaName"]
        # add local data
        national_data[i-1].update(local_data[i-1])
        # rename local keys
        national_data[i-1]["local_newCasesBySpecimenDate"] = \
            national_data[i-1]["newCasesBySpecimenDate"]
        national_data[i-1]["local_areaType"] = national_data[i-1]["areaType"]
        national_data[i-1]["local_areaName"] = national_data[i-1]["areaName"]
        # clean up bad data
        del national_data[i-1]["newCasesBySpecimenDate"]
        del national_data[i-1]["areaType"]
        del national_data[i-1]["areaName"]
    return national_data


def covid_API_request (location = configuration["location"], location_type = "ltla"):
    """Polls the public COVID API to request data and stores it in a pair of files.

    Args:
        location (str, optional): location within nation. Defaults to "Exeter".
        location_type (str, optional): type of location. Defaults to "ltla".

    Returns:
        dictionary data_all: compiled data of every request as a single dictionary

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
        "areaType" : "areaType",
        "areaName" : "areaName",
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
    # Commented out as 2+ exports is unnecessary with the later method,
    # but keeping the code may be useful for debugging in the future
    #export_file = open('data_national.json', 'w', encoding="UTF-8")
    #json.dump(data_national, export_file, indent = "")
    #export_file = open('data_local.json', 'w', encoding="UTF-8")
    #json.dump(data_local, export_file, indent = "")

    data_all = dictionary_combiner(data_local, data_national)
    # return all data
    return data_all


def process_covid_data(covid_data):
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
    for current_line in covid_data:
        # make sure all expected keynames are present
        if len(current_line) == 9:
            logging.debug("Current line in covid data: %s" , current_line)
            # process data by checking if data is valid to use

            if current_line["cumDailyNsoDeathsByDeathDate"] \
                is not None \
                    and not total_deaths_assigned:

                # this if statement only assigns the first satisfactory value for deaths, as
                # total_deaths is cumulative
                total_deaths = current_line["cumDailyNsoDeathsByDeathDate"]
                # switch latch post assignment to prevent reassigning a wrong number in future loops
                total_deaths_assigned = True

            if current_line["hospitalCases"] \
                is not None \
                    and not current_hospital_cases_assigned:

                current_hospital_cases = current_line["hospitalCases"]
                # switch latch post assignment to prevent reassigning a wrong number in future loops
                current_hospital_cases_assigned = True

            if current_line["national_newCasesBySpecimenDate"] \
                is not None \
                    and not national_last7days_cases_assigned:

                if not national_first_date_passed:
                    # switch latch if the first number (incomplete data) has just been read
                    national_first_date_passed = True

                else:
                    # find new total cases and increment days
                    national_last7days_cases = \
                        national_last7days_cases + current_line["national_newCasesBySpecimenDate"]
                    national_days_summed += 1

                    # switch latch if data summed for the past week
                    if national_days_summed == 7:
                        national_last7days_cases_assigned = True

            if current_line["local_newCasesBySpecimenDate"] \
                is not None \
                    and not local_last7days_cases_assigned:

                if not local_first_date_passed:
                    # switch latch if the first number (incomplete data) has just been read
                    local_first_date_passed = True

                else:
                    # find new total cases and increment days
                    local_last7days_cases = \
                        local_last7days_cases + current_line["local_newCasesBySpecimenDate"]
                    local_days_summed += 1
                    # switch latch if data summed for the past week
                    if local_days_summed == 7:
                        local_last7days_cases_assigned = True

        # check all tasks complete; if so, end function and return variables
        # logic here checks if all 4 values are True ie. have the related variables been assigned
        if total_deaths_assigned and \
            current_hospital_cases_assigned and \
                national_last7days_cases_assigned and \
                    local_last7days_cases_assigned:
            logging.info ("All tasks in process_covid_data complete")
            logging.debug ("Local last 7 days cases: %s" , local_last7days_cases)
            logging.debug ("National last 7 days cases: %s" , national_last7days_cases)
            logging.debug ("Current hospital cases: %s" , current_hospital_cases)
            logging.debug ("Total deaths: %s" , total_deaths)
            logging.info ("Data returned")
            return (total_deaths, current_hospital_cases, \
                national_last7days_cases, local_last7days_cases)

    # function should always complete the earlier check by the end of the given json
    # if not, the for loop ends and this line will be printed
    logging.warning ("Error: not all functions in process_covid_data completed")


def get_covid_data(update_name = None):
    """Function to call all live functions to get up-to-date COVID data

    Returns:
        int: all useful COVID data for display in dashboard
        deaths, hospital_cases, national_last_week_cases, local_last_week_cases
    """
    logging.info("get_covid_data request acknowledged...")
    deaths, hospital_cases, \
        national_last_week_cases, local_last_week_cases = \
            process_covid_data (covid_API_request())
    """
    if update_name:
        with open('updates.json', 'r', encoding = "UTF-8") as updates_file:
            try:
                updates = json.load(updates_file)
                logging.info("Updates loaded")
            except JSONDecodeError:
                updates = []
                logging.error("Updates file empty; should contain update to cancel")
        logging.info ("Update remove request found:")
        update_count = 0
        for update in updates:
            logging.debug ("Checking update: %s", str(update))
            if update["title"] == update_name:
                logging.info ("Update found; deleting")
                del updates[update_count]
                with open ("updates.json", "w", encoding = "UTF-8") as updates_file:
                    json.dump (updates, updates_file, ensure_ascii=False, indent="")
                #yield redirect ("/index")
            update_count += 1
    """
    return deaths, hospital_cases, national_last_week_cases, local_last_week_cases


def schedule_covid_updates(update_interval, update_name):
    # error in logic: the same updates can be scheduled more than once; they will run
    # at the same time, so this will not affect functionality, but may become performance-heavy
    logging.info("function schedule_covid_updates called...")
    with open('updates.json', 'r', encoding = "UTF-8") as updates_file:
        try:
            updates = json.load(updates_file)
            logging.info("Updates loaded for scheduler")
        except JSONDecodeError:
            logging.critical("Updates failed to load")

    for update in updates:
        logging.debug("Checking update %s", update)
        if update["title"] == update_name:
            logging.debug("Update match found, scheduling: %s", update)
            sched_update = update

            if sched_update["repeat"]:
                logging.debug("Repeat marker identified")
                #repeat_update = sched.scheduler(timefunc = time.monotonic)
                flask_update.enter (update_interval,
                                    0,
                                    schedule_covid_updates,
                                    argument = (86400, update_name)
                                    )
                #repeat_update.run()
                logging.info ("Repeated update scheduled")
                # these lines do not pass the variable to delete the update; this allows
                # events to repeat more than once
                if sched_update["update_covid?"] and sched_update["update_news?"]:
                    logging.debug("Repeat combined update found to schedule")
                    #news_update = sched.scheduler(timefunc = time.monotonic)
                    #covid_update = sched.scheduler(timefunc = time.monotonic)
                    flask_update.enter(update_interval,
                                    1,
                                    update_news
                                    )
                    flask_update.enter(update_interval,
                                    2,
                                    get_covid_data
                                    )
                    #news_update.run()
                    #covid_update.run()
                    logging.info("Repeat combined update scheduled: %s", update_name)
                elif sched_update["update_covid?"] and not sched_update["update_news?"]:
                    logging.debug("Repeat COVID update found to schedule")
                    #covid_update = sched.scheduler(timefunc = time.monotonic)
                    flask_update.enter(update_interval,
                                    1,
                                    get_covid_data,
                                    )
                    #covid_update.run()
                    logging.info("Repeat COVID update scheduled: %s", update_name)
                elif not sched_update["update_covid?"] and sched_update["update_news?"]:
                    logging.debug("Repeat news update found to schedule")
                    #news_update = sched.scheduler(timefunc = time.monotonic)
                    flask_update.enter(update_interval,
                                    2,
                                    update_news
                                    )
                    #news_update.run()
                    logging.info("Repeat news update scheduled: %s", update_name)
                else:
                    logging.error("Error in scheduling repeat update: no action selected")
            else:
                # passing update_name to the functions allows them to remove the update at runtime
                if sched_update["update_covid?"] and sched_update["update_news?"]:
                    logging.debug("Combined update found to schedule")
                    #news_update = sched.scheduler(timefunc = time.monotonic)
                    #covid_update = sched.scheduler(timefunc = time.monotonic)
                    flask_update.enter(update_interval,
                                    1,
                                    update_news,
                                    argument = (update_name)
                                    )
                    flask_update.enter(update_interval,
                                    2,
                                    get_covid_data,
                                    argument = (update_name)
                                    )
                    #news_update.run()
                    #covid_update.run()
                    logging.info("Combined update scheduled: %s", update_name)
                elif sched_update["update_covid?"] and not sched_update["update_news?"]:
                    logging.debug("COVID update found to schedule")
                    #covid_update = sched.scheduler(timefunc = time.monotonic)
                    flask_update.enter(update_interval,
                                    1,
                                    get_covid_data,
                                    argument = (update_name)
                                    )
                    #covid_update.run()
                    logging.info("COVID update scheduled: %s", update_name)
                elif not sched_update["update_covid?"] and sched_update["update_news?"]:
                    logging.debug("News update found to schedule")
                    #news_update = sched.scheduler(timefunc = time.monotonic)
                    flask_update.enter(update_interval,
                                    2,
                                    update_news,
                                    argument = (update_name)
                                    )
                    #news_update.run()
                    logging.info("News update scheduled: %s", update_name)
                else:
                    logging.critical("Error in scheduling updates: no action selected")
    logging.info ("Update scheduling complete")
    logging.info ("Updates run")
    logging.info ("Update queue: %s", flask_update.queue)
    return redirect ("/index")
    #print ("executed: ", new_event)



# run functions with local test data for CSV
#process_covid_csv_data (parse_csv_data ("nation_2021-10-28.csv"))
#get_covid_data_json()
#get_locations(parse_json_data())
#schedule_covid_updates(5, "test")
