#!/usr/bin/env python3

from typing import List, Tuple
import requests
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


def get_seven_day_average(data: List[float], dates: List[str]) -> Tuple[List[float], List[str]]:
    """ Calculates the 7-day averate of a given quantity over given time
        Arguments:
            data(list of numbers): data of which the average is taken
            dates(list of variable type X): dates corresponding to given data
        Return: seven_day_average_data, seven_day_average_dates
            seven_day_average_data(list of numbers): the 7-day averages
            seven_day_average_dates(list of var type X): corresponding dates
    """
    seven_day_average_data = []
    seven_day_average_dates = []

    for x in range(len(data)):
        if x >= 7:
            average = (data[x] + data[x-1] + data[x-2] + data[x-3]
                       + data[x-4] + data[x-5] + data[x-6]) / 7
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


def plot_positivity_rate(days: List[str], positive_percent: List[float], mass_positive_percent: List[float] = None):
    """ Plots the changing positivity rate with each day
        Arguments:
            days (list of dates): dates on which data was collected
            positive_percent (list of nums): positivity rates for each date
            mass_positive_percent (list of nums): positivity rates of Mass
    """
    sda_rate, sda_days = get_seven_day_average(positive_percent, days)

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


def plot_daily_positive_tests(days: List[str], daily_positive_tests: List[float]):
    """ Plots the number of positive test per day
        Arguments:
            days (list of dates): dates on which data was collected
            daily_positive_tests (list of nums): positive tests per day
    """
    sda_rate, sda_days = get_seven_day_average(daily_positive_tests, days)
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
    response_payload = requests.get(GIST_URL).json()["files"]["data.json"]["content"]
    api_data = json.loads(response_payload)
    data = []

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
    # Return formatted data
    return data


def update_local_data() -> List[Data_Point]:
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
                print("Updating local data")
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
    positive_percent = []

    for data_point in data:
        days.append(dt.strptime(data_point.date, '%m/%d/%Y').date())
        daily_positive_tests.append(data_point.positive_tests)
        daily_negative_tests.append(data_point.negative_tests)
        positive_percent.append(data_point.positive_rate)

    # Plot the positive rate
    plot_positivity_rate(days, positive_percent)

    # Plot the total number of positive cases
    plot_daily_positive_tests(days, daily_positive_tests)

    # Plot the total number of tests
    plot_tests_and_outcomes(days, daily_positive_tests, daily_negative_tests)


if __name__ == "__main__":
    main()
