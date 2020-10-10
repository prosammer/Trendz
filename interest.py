import pandas as pd
import os, requests, time, operator
from pytrends.request import TrendReq
import plotly.express as px
import pymysql.cursors
from sqlalchemy import create_engine, exc


# Set desired number of cycles (for easy testing)
numofcycles = 10


# Only needs to run once - all requests use this session
# Timezone is 240 (could be -240 as well?)
pytrends = TrendReq(hl='en-US', tz=-240,retries=2,backoff_factor=0.2,)



# Connect to the database

connection = pymysql.connect(host='localhost',
user='root',
password='Jura55ic5',
db='trends',
charset='utf8mb4',
cursorclass=pymysql.cursors.DictCursor)


# create sqlalchemy engine
engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
.format(user="root",
pw="Jura55ic5",
db="trends"))

def retrieve_keyword(cursor):
    # Read a single record
    sqlselect = "SELECT topic_title FROM keywords WHERE interest IS NULL ORDER BY 'id' DESC LIMIT 1;"
    cursor.execute(sqlselect)
    # Returns a list of key:value dicts with 'topic_title':keyword
    listofdicts = cursor.fetchall()
    # Turns list of dict into a single-item list
    resultlist = [f['topic_title'] for f in listofdicts]
    return resultlist


def find_interest(cursor):
    singlekeywordlist = retrieve_keyword(cursor)
    keyword = str(singlekeywordlist[0])
    print("Keyword type is: ",type(keyword), "Keyword is: ", keyword)

    time.sleep(3)
    pytrends.build_payload(kw_list=singlekeywordlist, timeframe='all', geo='CA')
    print("Commencing interest_over_time search...")
    interest_over_time_df = pytrends.interest_over_time()
    #Don't care about the isPartial column - dropping it
    df = interest_over_time_df.drop(columns=['isPartial'])
    print(df.tail())
    time.sleep(10)
    keywordattr = getattr(df, keyword)

    interest_dict = dict(zip(df.index, keywordattr))

    interest_data_insert = "UPDATE keywords SET interest=\"%s\" WHERE topic_title = \"%s\"" % (interest_dict,keyword)
    cursor.execute(interest_data_insert)
    print("Execute finished!")


if __name__ =='__main__':
    print("Number of Cycles to run: ", str(numofcycles))
    with connection.cursor() as cursor: 
        find_interest(cursor)
        connection.commit()
        connection.close()