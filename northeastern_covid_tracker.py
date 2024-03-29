#!/usr/bin/env python3

from typing import List, Tuple
import requests
from requests import ConnectTimeout, ConnectionError
from dataclasses import dataclass
import dataclasses
import matplotlib.pyplot as plt
from datetime import datetime as dt
import json
import os


DATA_PATH = "data"
DATA_FILE = os.path.join(DATA_PATH, "data.json")
GRAPH_PATH = "graphs"
GIST_URL = "https://api.github.com/gists/739ea390dcf28b58d8b36bba4ca88d68"

MIN_TESTS_FOR_SIGNIFICANCE = 50
UPDATE_THRESHOLD = 1800  # Seconds


@dataclass
class Data_Point:
    date: str
    tests_completed: int
    negative_tests: int
    negative_rate: float
    positive_tests: int
    positive_rate: float


def sum_weekly(list: List[int], index: int) -> int:
    """
    Sums a week's worth of data
    Arugments:
        list (list of nums): list of values to be summed
        index (int): starting index in list
    Return:
        integer sum of weekly value
    Raises:
        Value error if the list cannot be summed at the given index
    """
    if index >= 6:
        return (list[index] + list[index-1] + list[index-2] + list[index-3]
                + list[index-4] + list[index-5] + list[index-6])
    else:
        raise ValueError("Given index-list pair invalid")


def get_seven_day_average_positives(positive_tests: List[int], total_tests: List[int],
                                    dates: List[str]) -> Tuple[List[float], List[str]]:
    """ Calculates the 7-day averate of a given quantity over given time
        Arguments:
            positive_tests(list of numbers): postive test on a given day
            total_tests(list of numbers): total tests on a given day
            dates(list of variable type X): dates corresponding to given data
        Return: seven_day_average_data, seven_day_average_dates
            seven_day_average_data(list of numbers): the 7-day averages
            seven_day_average_dates(list of var type X): corresponding dates
    """
    seven_day_average_data = []
    seven_day_average_dates = []

    for x in range(len(positive_tests)):
        if x >= 7:
            weekly_total_positives = sum_weekly(positive_tests, x)
            weekly_total_tests = sum_weekly(total_tests, x)

            average = weekly_total_positives / weekly_total_tests * 100
            seven_day_average_data.append(average)
            seven_day_average_dates.append(dates[x])

    return seven_day_average_data, seven_day_average_dates


def get_seven_day_average_total(positive_tests: List[int],
                                dates: List[str]) -> Tuple[List[float], List[str]]:
    """ Calculates the 7-day averate of a given quantity over given time
        Arguments:
            positive_tests(list of numbers): postive test on a given day
            dates(list of variable type X): dates corresponding to given data
        Return: seven_day_average_data, seven_day_average_dates
            seven_day_average_data(list of numbers): the 7-day averages
            seven_day_average_dates(list of var type X): corresponding dates
    """
    seven_day_average_data = []
    seven_day_average_dates = []

    for x in range(len(positive_tests)):
        if x >= 7:
            weekly_total_positives = sum_weekly(positive_tests, x)

            average = weekly_total_positives / 7
            seven_day_average_data.append(average)
            seven_day_average_dates.append(dates[x])

    return seven_day_average_data, seven_day_average_dates


def save_standard_figure(filename: str):
    """ A wrapper that specifies the output path and format of graphs
        Arguments:
            filename (String): desired name of output file
    """
    plt.savefig(os.path.join(GRAPH_PATH, filename), dpi=500, pad_inches=.2,
                bbox_inches='tight', format="png")


def plot_positivity_rate(days: List[str], positive_percent: List[float],
                         positive_tests: List[int], total_tests: List[int],
                         mass_positive_percent: List[float] = None):
    """ Plots the changing positivity rate with each day
        Arguments:
            days (list of dates): dates on which data was collected
            positive_tests (list of integers): positive test each day
            total_tests (list of integers): total tests each day
            mass_positive_percent (list of nums): positivity rates of Mass
    """
    sda_rate, sda_days = get_seven_day_average_positives(positive_tests, total_tests, days)

    plt.plot(days, positive_percent, label="NEU Rate")
    plt.plot(sda_days, sda_rate, label="NEU 7-Day Average")
    plt.title("Covid-19 Positive Test Rate at Northeastern")
    plt.ylabel("% Positive Tests")
    plt.xlabel("Date")
    plt.xticks(rotation=-20)
    plt.legend(loc="upper right")
    plt.ylim(ymin=0.0)
    plt.xlim(xmin=days[0])
    save_standard_figure("covid_positive_rate_chart.png")
    if mass_positive_percent is not None:
        plt.plot(days, mass_positive_percent, label="Mass Rate")
        plt.legend(loc="upper right")
        save_standard_figure("covid_positive_rate_chart_mass.png")
    plt.clf()


def plot_daily_positive_tests(days: List[str], daily_positive_tests: List[int]):
    """ Plots the number of positive test per day
        Arguments:
            days (list of dates): dates on which data was collected
            daily_positive_tests (list of nums): positive tests per day
            total_test (list of nums): total tests on a given day
    """
    sda_rate, sda_days = get_seven_day_average_total(daily_positive_tests, days)
    plt.bar(days, daily_positive_tests, .95)
    plt.plot(sda_days, sda_rate, label="NEU 7-Day Average", color='r')
    plt.ylabel("Positive Tests")
    plt.xlabel("Date")
    plt.title("Daily New Covid-19 Cases")
    plt.xticks(rotation=-20)
    plt.xlim(xmin=days[0])
    save_standard_figure("covid_positives_chart.png")
    plt.clf()


def plot_tests_and_outcomes(days: List[str], daily_positive_tests: List[float], daily_negative_tests: List[float]):
    """ Plots the changing positivity rate with each day
        Arguments:
            days (list of dates): dates on which data was collected
            daily_positive_tests (list of nums): positive tests for each date
            daily_negative_tests (list of nums): negative tests for each date
    """
    plt.bar(days, daily_negative_tests, .8, label="Negative")
    plt.bar(days, daily_positive_tests, .8, bottom=daily_negative_tests,
            label="Positive")
    plt.ylabel("Test Performed")
    plt.xlabel("Date")
    plt.title("Covid-19 Tests Performed")
    plt.legend(loc="upper left")
    plt.xticks(rotation=-20)
    plt.xlim(xmin=days[0])
    save_standard_figure("covid_tests_performed.png")
    plt.clf()


def get_data_from_api() -> List[Data_Point]:
    """ Gets the most up to date covid stats from Northeastern's Dashboard
        Return: data
            data(list of Data_Points): all of the neu data, formatted
    """
    data = []

    try:
        response_payload = requests.get(GIST_URL).json()["files"]["data.json"]["content"]
        api_data = json.loads(response_payload)

        for entry in api_data:
            date = entry["date"]
            formatted_date = f"{date[5:7]}/{date[-2:]}/{date[:4]}"
            tests_given = int(entry["total_tests"])
            if tests_given == 0 or tests_given < MIN_TESTS_FOR_SIGNIFICANCE:
                # Ignore extraneous or unrepresentative data
                continue
            negative_tests = int(entry["negative_tests"])
            positive_tests = int(entry["positive_tests"])

            data.append(Data_Point(formatted_date, tests_given, negative_tests,
                                   negative_tests / tests_given * 100,
                                   positive_tests,
                                   positive_tests / tests_given * 100))

    except ConnectionError or ConnectTimeout:
        print("Connection error, data could not be updated")

    # Return formatted data
    return data


def update_local_data() -> List[Data_Point]:
    """ Get data from API and store/update a local copy
        Return:
            data (List of Data_Point): covid data formatted as local data type
    """
    print("Updating local data")

    # Get data from NEU
    data = get_data_from_api()

    # Store the data locally
    with open(DATA_FILE, "w+") as data_file:
        adjusted_data = []
        for point in data:
            adjusted_data.append(dataclasses.asdict(point))
        data_file.write(json.dumps([str(dt.now()), adjusted_data]))
    return data


def main():
    """
    Use local data or update data from API to plot various graphs
    reflecting the covid testing stats at Northeastern.
    """
    data = []

    # Ensure local files exist
    if not os.path.isdir(DATA_PATH):
        os.mkdir(DATA_PATH)
    if not os.path.isdir(GRAPH_PATH):
        os.mkdir(GRAPH_PATH)

    # Check for and update data
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as local_data_file:
            timestamp, local_data = json.load(local_data_file)
            delta = dt.now() - dt.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')

            # Check if data is more than 30 minutes old
            if (delta.total_seconds() > UPDATE_THRESHOLD):
                data = update_local_data()

            else:
                for point in local_data:
                    data.append(Data_Point(**point))
    else:
        data = update_local_data()

    # Get relevent data for display
    days = []
    daily_positive_tests = []
    daily_negative_tests = []
    daily_total_tests = []
    positive_percent = []

    for data_point in data:
        days.append(dt.strptime(data_point.date, '%m/%d/%Y').date())
        daily_positive_tests.append(data_point.positive_tests)
        daily_negative_tests.append(data_point.negative_tests)
        daily_total_tests.append(data_point.tests_completed)
        positive_percent.append(data_point.positive_rate)

    # Plot the positive rate
    plot_positivity_rate(days, positive_percent, daily_positive_tests, daily_total_tests)

    # Plot the total number of positive cases
    plot_daily_positive_tests(days, daily_positive_tests)

    # Plot the total number of tests
    plot_tests_and_outcomes(days, daily_positive_tests, daily_negative_tests)


if __name__ == "__main__":
    main()
