import argparse
from os import path, makedirs
from time import sleep
from datetime import datetime, timedelta
from csv import writer as csv_writer

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException


class TweetScraper:
    """Class used to scrape twitter data from "Explore" page.html

    After initialization, can run the ``TweetScraper.run_scraper()`` method
    to run the full scraping process using the parameters/attributes from the
    object initialization.

    Attributes
    ----------
    chromedriver_path : str
        Filepath to chromedriver executable.
    coin_name : str
        Coin name. E.g. "Bitcoin", "Ethereum", "Dogecoin", etc.
    coin_abbrv : str
        Coin abbreviation. E.g. "BTC", "ETH", "DOGE", etc.
    date_start : str
        Start date in range of days to individually scrape.
    date_end : str
        End date in range of days to individually scrape.
    min_faves : int, default 0
        Minimum number of favorites/likes for searched tweets.
    min_retweets : int, default 0
        Minimum number of retweets for searched tweets
    min_replies : int, default 0
        Minimum number of replies for searched tweets.
    page : str, {"top", "latest"}, default "top"
        "Top" or "Latest" tweet page.
    language : str, default "en"
        Language of tweets.

    Methods
    -------
    query_string(date_since, date_until)
        Build Twitter URL with query string based on object attributes.
    date_rng(start, end)
        Create list of string dates between `start` and `end` dates.
    scrape_visible_data(driver, css_selector, text=True, scroll=False)
        Scrapes visible data (datetime or tweet text) from browser.
    scrape_full_page(driver)
        Scrape all tweets and datetimes by scrolling Twitter Explore page.
    export_csv(filename, data, folder=None)
        Write data to csv file.
    run_scraper()
        Run full scraping process for all individual days in date range
        between ``obj.date_start`` and ``obj.date_end`` attributes.
    """

    def __init__(self,
                 chromedriver_path: str,
                 date_start: str,
                 date_end: str,
                 coin_name: str,
                 coin_abbrv: str,
                 min_faves: int = 0,
                 min_retweets: int = 0,
                 min_replies: int = 0,
                 page: str = "top",
                 language: str = "en"):
        """
        Parameters
        ----------
        chromedriver_path : str
            Filepath to chromedriver executable.
        coin_name : str
            Coin name. E.g. "Bitcoin", "Ethereum", "Dogecoin", etc.
        coin_abbrv : str
            Coin abbreviation. E.g. "BTC", "ETH", "DOGE", etc.
        date_start : str
            Start date in range of days to individually scrape.
        date_end : str
            End date in range of days to individually scrape.
        min_faves : int, default 0
            Minimum number of favorites/likes for searched tweets.
        min_retweets : int, default 0
            Minimum number of retweets for searched tweets
        min_replies : int, default 0
            Minimum number of replies for searched tweets.
        page : str, {"top", "latest"}, default "top"
            "Top" or "Latest" tweet page.
        language : str, default "en"
            Language of tweets.

        Raises
        ------
        ValueError
            If ``date_start`` or ``date_end`` cannot be converted to correct
            datetime
        """
        try:
            self.date_start = datetime.strptime(date_start, "%Y-%m-%d")
            self.date_end = datetime.strptime(date_end, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                "Date format must be '%Y-%m-%d'"
            )
        self.chromedriver_path = chromedriver_path
        self.coin_name = coin_name
        self.coin_abbrv = coin_abbrv
        self.min_faves = min_faves
        self.min_retweets = min_retweets
        self.min_replies = min_replies
        self.page = page
        self.language = language

    def query_string(self, date_since: str, date_until: str) -> str:
        """Build Twitter URL with query string based on object's
        initialized attributes.

        Parameters
        ----------
        date_since : str
            Beginning of time period in search url string. Based on UTC time
            for given day. Must be formatted in string like "2022-01-01"
            ("YYYY-MM-DD").
        date_until : str
            End of time period in search url string. Based on UTC time for
            given day. Must be formatted in string like "2022-01-02"
            ("YYYY-MM-DD").

        Returns
        -------
        str
            URL with query string for twitter search.
        """
        url = (
            f"https://twitter.com/search?q=({self.coin_name}"
            f"%20OR%20{self.coin_abbrv})"
            f"%20min_replies%3A{self.min_replies}"
            f"%20min_faves%3A{self.min_faves}"
            f"%20min_retweets%3A{self.min_retweets}"
            f"%20lang%3A{self.language}"
            f"%20until%3A{date_until}"
            f"%20since%3A{date_since}"
            f"&src=typed_query&f={self.page.lower()}"
        )
        return url

    @staticmethod
    def date_rng(start: datetime, end: datetime):
        """Create list of string dates between `start` and `end` dates.

        Returned date format "YYYY-MM-DD".

        Parameters
        ----------
        start : datetime
        end : datetime

        Returns
        -------
        list of strs
            All days between (and including) `start` and `end`.
            String dates formatted like "YYYY-MM-DD".
        """
        delta = end - start  # timedelta obj
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(delta.days+1)]
        return days

    @staticmethod
    def scrape_visible_data(driver,
                            css_selector: str,
                            text: bool = True,
                            scroll: bool = False) -> list:
        """Scrape visible data (datetime or tweet text) from browser.

        If ``text`` is False, will return datetimes (as strings). If True,
        function will return text of entire tweet including:
            * User name
            * Account Name (e.g. "@twitter")
            * Number of replies
            * Number of retweets
            * Number of favorites
            * Tweet body, user name, account handle within a quote/nested tweet

        Returned text will be one long string with key elements of tweet
        separable by new line character "\n".

        Parameters
        ----------
        driver : selenium web driver object
        css_selector : str
            Used to find tweets on the webpage.
        text : bool, default True
            If this is False the function will return list of datetimes (as
            strings) for each tweet.
        scroll : bool, default False
            If True, have browser (``driver``) scroll page to the last element.

        Returns
        -------
        list
            Either list of string datetimes OR list of tweet texts dependent on
            the ``text`` param.
        """
        web_elems = driver.find_elements_by_css_selector(css_selector)
        if not text:
            data = [time.get_attribute("datetime") for time in web_elems]
        else:
            data = [element.text for element in web_elems]

        if scroll:
            last_elem_loc = web_elems[-1].location
            x = last_elem_loc["x"]
            y = last_elem_loc["y"]
            driver.execute_script(f"window.scrollTo({x}, {y})")

        return data

    @staticmethod
    def scrape_full_page(driver) -> set:
        """Scrape all tweets and datetimes by scrolling Twitter Explore page.

        Parameters
        ----------
        driver : selenium web driver object

        Returns
        -------
        set
            Set of tuples. Tuples formatted like (datetime: str, tweet: str).
        """
        full_tweets = set()
        css = (
            "div.css-1dbjc4n.r-1iusvr4.r-16y2uox.r-1777fci.r-kzbkwu"
        )
        num_tweets = len(full_tweets)
        break_count = 0
        num_scrolls = 0
        while True:
            # Pause all videos before scraping or will get duplicates
            # on any tweets with videos
            driver.execute_script(
                "document.querySelectorAll('video').forEach(vid => vid.pause());"
            )
            sleep(1.5)
            datetimes = TweetScraper.scrape_visible_data(
                driver,
                css_selector="a time",
                text=False)
            tweets = TweetScraper.scrape_visible_data(driver, css_selector=css, scroll=True)
            assert len(tweets) == len(datetimes), (
                "DIFFERENT NUMBER OF TWEETS AND DATETIMES"
            )
            full_tweets.update(set(zip(datetimes, tweets)))
            if num_tweets == len(full_tweets):
                break_count += 1
                if break_count >= 3:
                    break
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
            else:
                break_count = 0

            num_scrolls += 1
            if num_scrolls > 3200:
                raise Exception(
                    "MAXIMUM NUMBER OF SCROLLS REACHED"
                )
            num_tweets = len(full_tweets)

        return full_tweets

    @staticmethod
    def export_csv(filename: str, data, folder: str = None) -> None:
        """Write data to csv file.

        Parameters
        ----------
        filename : str
        data : iterable
        folder : str, optional
            Export file to folder inside of working directory. If folder
            doesn't already exist, it will be created.
        """
        if folder:
            if not path.exists(folder):
                makedirs(folder)
            filename = folder + '/' + filename

        with open(filename, "w") as f:
            writer = csv_writer(f)
            writer.writerow(["datetime", "tweet"])
            writer.writerows(data)

    def run_scraper(self):
        """Run full scraping process.

        Loops through each day in the range between ``obj.date_start`` and
        ``obj.date_end`` making a url request for each individual day. For each
        date, the webdriver will scroll down the page to render the max amount
        of tweets and scrape the info. The info for each date scraped will be
        exported to a folder in the working directory called "exports/". Each
        file will be named with the coin abbreviation (``obj.coin_abbrv``) and
        date (the until/end date).
        """
        options = Options()
        options.headless = False
        driver = webdriver.Chrome(
            self.chromedriver_path,
            options=options
        )

        dates = self.date_rng(self.date_start, self.date_end)
        i = 0
        err_counter = 0
        with open("errors.log", "a") as logf:
            while i < len(dates)-1:
                try:
                    start_day = dates[i]
                    end_day = dates[i+1]
                    url = self.query_string(
                        date_since=start_day,
                        date_until=end_day,
                    )
                    driver.get(url)
                    delay = 30

                    WebDriverWait(
                        driver,
                        timeout=delay
                    ).until(lambda d: d.find_element_by_tag_name("time"))
                    sleep(7)

                    data = self.scrape_full_page(driver)
                except TimeoutException:
                    print(f"Timeout - start:'{start_day}', end: '{end_day}'")
                    logf.write(f"\nTimeout - '{end_day}'")
                    data = []  # Export blank file if no tweets meet threshold
                except WebDriverException:
                    err_counter += 1
                    if err_counter >= 5:
                        print("Error Counter >= threshold. FUNCTION TERMINATED")
                        break
                    continue
                except Exception as err:
                    logf.write(f"\nEnd Date: {end_day}. Error: '{err}'")
                    print(f"Error logged {end_day}")
                    i += 1
                    continue

                filename = f"{self.coin_abbrv}_tweets_{end_day}.csv"
                folder = f"Tweets/{self.coin_name}"
                self.export_csv(filename=filename, data=data, folder=folder)
                sleep(1)
                i += 1

        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "chromedriver_path",
        type=str,
        help="Filepath to the ChromeDriver executable."
    )
    parser.add_argument(
        "coin_name",
        type=str,
        help="Name of coin to search for in tweets. Cannot contain any spaces."
    )
    parser.add_argument("coin_abbrv",
        type=str,
        help="Abbreviation of coin to search for in tweets. Cannot contain any spaces."
    )
    parser.add_argument("-start",
        "--start-date",
        dest="date_start",
        type=str,
        default="2021-12-31",
        help="First day to search. Date format: 'YYYY-MM-dd'."
    )
    parser.add_argument("-end",
        "--end-date",
        dest="date_end",
        type=str,
        default="2022-01-01",
        help="Last date to search. Date format: 'YYYY-MM-DD'."
    )
    parser.add_argument("-faves",
        "--min-faves",
        dest="min_faves",
        type=int,
        default=0,
        help="Minimum threshold for number of favorites/likes on searched tweets."
    )
    parser.add_argument("-rtwts",
        "--min-retweets",
        dest="min_retweets",
        type=int,
        default=0,
        help="Minimum threshold for number of retweets on searched tweets."
    )
    parser.add_argument("-replies",
        "--min-replies",
        dest="min_replies",
        type=int,
        default=0,
        help="Minimum threshold for number of replies on searched tweets."
    )
    parser.add_argument("-page",
        dest="page",
        type=str,
        default="top",
        help="'Top' or 'Latest' tweet page to search on."
    )

    args = parser.parse_args()
    if " " in args.coin_name:
        raise ValueError(
            "No spaces allowed in 'coin_name'"
        )
    if " " in args.coin_abbrv:
        raise ValueError(
            "No spaces allowed in 'coin_abbr'"
        )
    if args.page.lower() not in {"top", "latest"}:
        raise ValueError(
            "'page' argument must be 'top' or 'latest'"
        )

    CL_PARAMS = {
        "chromedriver_path": args.chromedriver_path,
        "date_start": args.date_start,
        "date_end": args.date_end,
        "coin_name": args.coin_name,
        "coin_abbrv": args.coin_abbrv,
        "min_faves": args.min_faves,
        "min_retweets": args.min_retweets,
        "min_replies": args.min_replies,
        "page": args.page
    }

    scraper = TweetScraper(**CL_PARAMS)
    scraper.run_scraper()



