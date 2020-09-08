from selenium import webdriver
from selenium.webdriver.chrome.options import Options  
from dataclasses import dataclass
import matplotlib.pyplot as plt

@dataclass
class Data_Point:
    date: str
    tests_completed: int
    negative_tests: int
    negative_rate: int
    positive_tests: int
    positive_rate: int
    mass_positive_rate: int


def get_seven_day_average(data, dates):
    """ Calculates the 7-day averate of a given quantity over given time
        Arguments:
            data(list of numbers): data of which the average is taken
            dates(list of variable type X): dates corresponding to given data
        Return: seven_day_average_data, seven_day_average_dates
            seven_day_average_data(list of numbers): the 7-day averages
            seven_day_average_dates(list of variable type X): dates corresponding to 7-day averages
    """
    seven_day_average_data = []
    seven_day_average_dates = []

    for x in range(len(data)):
        if x < 7:
            pass
        else:
            average = (data[x] + data[x-1] + data[x-2] + data[x-3]
                    + data[x-4] + data[x-5] + data[x-6]) / 7
            seven_day_average_data.append(average)
            seven_day_average_dates.append(dates[x])
    return seven_day_average_data, seven_day_average_dates
    

def get_data_from_neu_dashboard():
    """ Gets the most up to date covid stats from Northeastern's Dashboard
        Return: data
            data(list of Data_Points): all of the neu data, formatted
    """
    # Open the driver
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)

    # Get page elements
    driver.get("https://news.northeastern.edu/coronavirus/reopening/testing-dashboard/")

    # Check that the correct page is gotten
    if "Testing Dashboard" not in driver.title:
        print("\nWebpage not found\nExiting program")
        driver.quit()
        return

    # Get table from elements
    table = driver.find_element_by_tag_name("table")
    rows = table.find_elements_by_tag_name("tr")

    # Store the data in array form
    data = []
    for row in reversed(rows[1:]):
        points = row.text.split(" ")
        data.append(Data_Point(points[0],
                               int(points[1]),
                               int(points[2]),
                               float(points[3][:-1]),
                               int(points[4]),
                               float(points[5][:-1]),
                               float(points[6][:-1])))

    # Quit the driver
    driver.quit()

    # Return formatted data
    return data


def main():
    # Get data
    data = get_data_from_neu_dashboard()

    # Get relevent data
    days = []
    positive_percent = []
    mass_positive_percent = []

    for datum in data:
        days.append(datum.date)
        positive_percent.append(datum.positive_rate)
        mass_positive_percent.append(datum.mass_positive_rate)

    sda_rate, sda_days = get_seven_day_average(positive_percent, days)

    # Plot the data
    plt.plot(days, positive_percent, label="NEU Rate")
    plt.plot(sda_days, sda_rate, label="NEU 7-Day Average")
    plt.title("Coronavirus Positive Test Rate at Northeastern")
    plt.ylabel("% Positive Tests")
    plt.xlabel("Date")
    plt.xticks(rotation=-30)
    plt.legend(loc="upper right")
    plt.savefig("covid_chart.png", dpi=500, format='png')
    plt.plot(days, mass_positive_percent, label="Mass Rate")
    plt.legend(loc="upper right")
    plt.savefig("covid_chart_with_mass.png", dpi=500, format='png')


if __name__ == '__main__':
    main()