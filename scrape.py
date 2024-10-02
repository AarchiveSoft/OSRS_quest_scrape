import os
import sqlite3
import sys

import dateutil.parser
from dateutil import parser

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Scraper:
    """
    :class:`Scraper` is a class that is used to scrape the quests list from the Old School RuneScape website and store the information in a database.

    Methods:
    ---------
    __init__(self)
        Initializes the `Scraper` class with a `driver` attribute set to `None`.

    main(self)
        This method is the main entry point of the program. It sets up the database, initializes the driver, and navigates to the given website.

    setup_driver(self)
        Sets up the webdriver. Returns an instance of webdriver.Chrome if the driver setup is successful, otherwise returns None.

    setup_db(self)
        Sets up the database by creating a table if it doesn't exist.

    scrape(self)
        Scrapes the quests list from the Old School RuneScape website.

    Raises:
    -------
    Exception
        If an error occurs during the driver setup.

    Attributes:
    -----------
    driver
        An instance of the webdriver.Chrome class.

    conn
        Connection object for the SQLite database.

    c
        Cursor object for executing SQLite commands.
    """
    def __init__(self):
        self.driver = None

    def main(self):
        """
        This method is the main entry point of the program. It sets up the database, initializes the driver, and navigates
        to the given website.

        :return: None
        """

        self.setup_db()
        self.driver = self.setup_driver()

        self.scrape()

    def setup_driver(self):
        """
        :return: An instance of webdriver.Chrome if the driver setup is successful, otherwise None.
        """
        if getattr(sys, "frozen", False):
            # Running as packaged executable, driver is in same directory
            base_path = sys._MEIPASS
        else:
            # Running as normal script, driver is in parent directory
            base_path = os.path.dirname(os.path.abspath(__file__))
            # base_path = os.path.dirname(base_path)
        chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.path.join(base_path, 'chrome', 'win64-118.0.5993.70', 'chrome-win64',
                                                      'chrome.exe')

        service = Service(chromedriver_path)

        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def setup_db(self):
        """
        Setup the database by creating a table if it doesn't exist

        :return: None
        """
        self.conn = sqlite3.connect('OSRS_Quests.db')
        self.c = self.conn.cursor()

        self.c.execute('''CREATE TABLE IF NOT EXISTS quests
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        number INTEGER,
        name TEXT,
        difficulty TEXT,
        length TEXT,
        quest_points INTEGER,
        series TEXT,
        release_date DATE,
        members BOOLEAN,
        requirements TEXT,
        rewards TEXT,
        guide TEXT,
        link TEXT,
        UNIQUE(number, name)
        )
        ''')

        self.conn.commit()

    def scrape(self):
        """
        Scrapes the quests list from the Old School RuneScape website.

        :return: None
        """
        wait = WebDriverWait(self.driver, 10)

        self.driver.get("https://oldschool.runescape.wiki/w/Quests/List")

        f2p_quest_board = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body > div:nth-child(3) > "
                                                                                        "div:nth-child(5) > div:nth-child(7) > div:nth-child(1) > table:nth-child(7)")))
        f2p_quest_elements = f2p_quest_board.find_element(By.TAG_NAME, 'tbody')
        f2p_quests = f2p_quest_elements.find_elements(By.TAG_NAME, 'tr')

        # for quest in f2p_quests:
        #     print(quest.text)

        for quest in f2p_quests:
            number_text = quest.find_element(By.TAG_NAME, 'td').text
            number = int(number_text)
            attributes = quest.find_elements(By.TAG_NAME, 'td')
            name_element = attributes[1]
            name = name_element.get_attribute('title')
            link = name_element.get_attribute('href')

            difficulty = attributes[2].text
            length = attributes[3].text
            quest_points = int(attributes[4].text)

            # Handling 'N/A' series:
            if attributes[5].text != 'N/A':
                series = attributes[5].text
            else:
                series = "N/A"

            release_date = dateutil.parser.parse(attributes[6].text)
            members = False
            requirements = ""
            rewards = ""
            guide = ""

            # insert into db
            self.c.execute('''
                INSERT INTO quests (number, name, difficulty, length, quest_points, series, release_date, members, link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (number, name, difficulty, length, quest_points, series, release_date, members, link))
            self.conn.commit()

        self.driver.quit()


if __name__ == "__main__":
    scraper = Scraper()
    scraper.main()
