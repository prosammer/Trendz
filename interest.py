import pandas as pd
import os,sys,requests,time,operator,logging
from pytrends.request import TrendReq
import plotly.express as px
import pymysql.cursors
import fire


# TODO: Reduce to certain categories (in keywords.py)
# TODO: Figure out why df csv isnt updating into mysql (bc I can pull keywords from sql just fine?)
# TODO: Use proxylist when CLI arg set to local. Don't use when set to remote/

# Set desired number of cycles (for easy testing)
numofcycles = 10


#BlazingSEO proxy list - uses port 4444 for username/password based auth, and 3128 for IP based auth.


proxylist = ['https://104.168.51.141:3128','https://192.186.134.157:3128','https://192.3.214.40:3128','https://104.144.220.10:3128','https://104.144.28.167:3128','https://172.245.181.226:3128','https://192.210.185.193:3128','https://23.236.232.162:3128','https://23.254.68.49:3128','https://23.94.176.161:3128','https://69.4.90.17:3128','https://107.172.94.128:3128','https://138.128.84.159:3128','https://192.186.161.228:3128','https://192.241.64.90:3128','https://192.241.80.170:3128','https://198.12.80.148:3128','https://198.23.217.80:3128','https://23.250.94.234:3128','https://45.72.0.245:3128']



# Sets which address to use, and if proxies should be used, based on CLI input
def setloc(location):
    location=location
    logging.info(f"Your chosen location is: {location}")
    if location == "digitalocean":
        host='private-db-mysql-tor1-72034-do-user-8152651-0.b.db.ondigitalocean.com'
        pytrends = TrendReq(hl='en-US', tz=-240,retries=2,backoff_factor=0.2,proxies=proxylist)
    elif location == "remote":
        host='db-mysql-tor1-72034-do-user-8152651-0.b.db.ondigitalocean.com'
        pytrends = TrendReq(hl='en-US', tz=-240,retries=2,backoff_factor=0.2)
    else:
        raise Exception("Must specify location: 'remote' or 'local'." )
    
    connection = pymysql.connect(host=host,
    user='doadmin',
    password=password2,
    port=25060,
    db='trends',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor)

    return connection, pytrends

def retrieve_keyword(cursor):
    # Read a single record
    sqlselect = "SELECT topic_title FROM keywords WHERE interest IS NULL ORDER BY 'id' DESC LIMIT 1;"
    cursor.execute(sqlselect)
    # Returns a list of key:value dicts with 'topic_title':keyword
    listofdicts = cursor.fetchall()
    # Turns list of dict into a single-item list
    resultlist = [f['topic_title'] for f in listofdicts]
    return resultlist


def find_interest(cursor,pytrends):
    singlekeywordlist = retrieve_keyword(cursor)
    keyword = str(singlekeywordlist[0])

    logging.info(f"Keyword is: {keyword}")

    logging.info("Commencing get_historical_interest search...")
    try:
        historical_df = pytrends.get_historical_interest(singlekeywordlist, frequency='daily', year_start=2010, month_start=1, day_start=1, hour_start=0, year_end=2020, month_end=8, day_end=1, hour_end=0, geo='CA', gprop='', sleep=3)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if historical_df.empty:
        logging.info(f"Keyword type: {type(keyword)}")
        logging.info(f"Not enough data for keyword: {keyword} deleting from table...")

        sql_query = "DELETE from keywords WHERE topic_title = '{}'".format(keyword)
        cursor.execute(sql_query)
    else:
        #Don't care about the isPartial column - dropping it
        df = historical_df.drop(columns=['isPartial'])
        #Removing the extra 0's from datetime
        df.index = pd.to_datetime(df.index, format = '%Y-%m-%d').strftime('%Y-%m-%d')
        logging.info(f"df.head is: \n {df.head()}")
        csv = df.to_csv()
        sql_query = "UPDATE keywords SET interest='{}' WHERE topic_title = '{}'".format(csv, keyword)
        cursor.execute(sql_query)
        connection.commit()

    logging.info("Execute finished!")
    


if __name__ =='__main__':
    logging.root.handlers = []
    logging.basicConfig(level=logging.DEBUG, handlers=[
        logging.FileHandler("debug.log", mode='w'),
        logging.StreamHandler(sys.stdout)])

    logging.info("Greetings, Pleb!")
    logging.info(f"Number of Cycles to run: {numofcycles}")
    
    connection, pytrends = fire.Fire(setloc)
    print(f"Connection type: {type(connection)}, connection string: {str(connection)}")
    print(f"pytrends type: {type(pytrends)}, pytrends string: {str(pytrends)}")
    time.sleep(3)
    with connection.cursor() as cursor: 
        for i in range(numofcycles):
                find_interest(cursor,pytrends)
                
        connection.close()
