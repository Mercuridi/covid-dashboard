README for Covid Dashboard

Summary
This project is a self contained COVID dashboard. It uses a Flask server to host a webpage locally that automatically queries up-to-date COVID data with a working news feed and functionality to schedule when the data and the news are updated.

Prerequisites
Developed in Python 3.9.9
UK Covid 19 API (Python)
API key for NewsAPI; free at https://newsapi.org/
Flask

Installation
Run:
pip install uk-covid19
pip install flask

Getting started
Check the installation folder for a set of files;
removed_articles.json
updates.json
sys.log

If these files are not present, create them. They should be present by default; check that they are empty.

To get started, run the module webcode.py. This will launch the flask website, and this can be accessed by default at the web address 127.0.0.1:5000/index.
To schedule an update to the news, data, or both, input the desired update time and whether it repeats under the central data column.
Both updates and news articles can be removed by clicking the cross in the upper-right corner of their respective box.

Developer documentation
sys.log contains the system log for the server and its respective code. Check here to see what the site has been doing.
updates.json contains the information for the updates stored in the website. Upon each load the website checks this file for updates to display.
removed-articles.json stores articles that have been removed by the user. Upon a news update or website refresh, this file is checked against to not show removed news articles again.

Author: Kai Barber-Harris
