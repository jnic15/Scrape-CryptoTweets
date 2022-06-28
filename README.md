## DESCRIPTION
This code was used as part of a larger group project in Georgia Tech's CSE 6242 Data and Visual Analytics class.

My group's objective was to analyze the correlation between top Twitter influencers tweet sentiment and coin pricing. Due to Twitter's API only giving limited historical data, we decided to scrape the data. This module scrapes as much data as Twitter will render in the browser for an unknown user (not signed into an account). In our scraping the scrolling limit of tweets per day scraped seemed to be around 100.

We used the Selenium library in Python to scrape data because of needing to scroll the page to render more and more tweets.

This can be easily run from the command line and will export scraped data to csv files. After the scraper runs for an individual day, the scraped data will be exported to a csv file in a created path ``{tweet_scrapt.py dir}/Tweets/{coin_name}``.

When running from the command line there are several optional arguments that can be used to modify the search.
- The two most important are the ``coin_name`` and ``coin_abbrv``. This allows a user to search for tweets that include either one. For example, using ``"Bitcoin"`` as the ``coin_name`` and ``"BTC"`` as the ``coin_abbrv`` would return Tweets that contain either "Bitcoin" OR "BTC".

- The start date (``-start``) and end date (``-end``) create a range of individual days to scrape. E.g. if you use a start date of 2022-01-01 and end date of 2022-01-03 you will get data files exported separately for both days 01/01/2022 and 01/02/2022.

- You can also set thresholds to filter and/or limit the tweets that are returned in the search. E.g. you can use use the arguments ``-faves 100 -rtwts 50 -replies 20`` and only tweets with at least 100 favorites/likes, 50 retweets, and 20 replies will come back from your search.

## INSTALLATION
1. Download `tweet_scrape.py` file from repository.
2. Install the required packages in `requirements.txt` using `pip`.<br>
`$ pip install -r requirements.txt`
3. Install Google Chrome (if not already on machine)<br>
https://www.google.com/chrome/downloads/

## EXECUTION (CLI)
1. Open a terminal/command prompt and change directory to directory containing `tweet_scrape.py`.

2. Enter on the command line enter <br>
`python tweet_scrape.py "Bitcoin" "btc" -start "2021-12-21" -end "2021-12-31" -faves 100`
    * To run for other coins just change `"Bitcoin"` to the coin name (e.g. "Dogecoin") and `"btc"` to the coin abbreviation (e.g. "doge").

3. This command should open an automated chrome browser and start scrolling and scraping data. Each individual date scraped in the date range should take about a minute or two. Here, about 10 days will be scraped and the data will be exported to 10 separate csv files.
