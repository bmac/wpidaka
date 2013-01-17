from datetime import date
from optparse import OptionParser
import requests
from bs4 import BeautifulSoup

def get_command_line_options():
    parser = OptionParser()
    parser.add_option("-q", "--quiet",
                  action="store_const", const=0, dest="verbose")
    parser.add_option("-v", "--verbose",
                  action="store_const", const=1, dest="verbose")
    parser.add_option("--dry-run",
                  action="store_true", dest="dry_run")
    parser.add_option("-m", "--meal", dest="meal", 
                      choices=['breakfast', 'lunch', 'dinner'],
                      help="This switch controls the meal this is posted to twitter.")
    (options, args) = parser.parse_args()
    return options


def request_todays_menu_html(date):
    payload = {'dt': date, 'venueName': 'Pulse On Dining Marketplace'}
    r = requests.get("http://www.dineoncampus.com/wpi/webtrition/webtrition.cfm", params=payload)
    return r.text



MENU_TABLE_CLASS = 'menu-content'
BREAKFAST_TABLE_ID = 'menu-tbl-1'
AFTERNOON_SNACK_TABLE_ID = 'menu-tbl-2'
LUNCH_TABLE_ID = 'menu-tbl-3'
DINNER_TABLE_ID = 'menu-tbl-4'
LATE_NIGHT_TABLE_ID = 'menu-tbl-5'

# iterate through a list pushing everything before the conditional is found into 
# the first partition. Then everything after the conditional is found into
# the second partition
def partition(iterable, func):
    first_partition = []
    second_partition = []
    partition_found = False
    for i in iterable:
        partition_found = partition_found or func(i)
        if partition_found:
            second_partition.append(i)
        else:
            first_partition.append(i)
    return (first_partition, second_partition)

def find_breakfast_items(soup):
    breakfast_table = soup.find(id=BREAKFAST_TABLE_ID)
    items = breakfast_table.find_all('span', 'item-name')
    items_text = [i.text.strip() for i in items]
    return items_text

def find_lunch_items(soup):
    lunch_table = soup.find(id=LUNCH_TABLE_ID)
    items = lunch_table.find_all('span', class_=['item-name', 'station-name'])
    (dull, interesting_items) = partition(items, 
                                          lambda x: x.text.strip().lower() == 'kitchen')
    items_text = [span.text.strip() for span in interesting_items if 'item-name' in span.attrs['class'] ]
    return items_text

def find_dinner_items(soup):
    dinner_table = soup.find(id=DINNER_TABLE_ID)
    items = dinner_table.find_all('span', class_=['item-name', 'station-name'])
    (dull, interesting_items) = partition(items, 
                                          lambda x: x.text.strip().lower() == 'kitchen')
    items_text = [span.text.strip() for span in interesting_items if 'item-name' in span.attrs['class'] ]
    return items_text


def format_items_message(items):
    header = 'Now serving: '
    elipsis = '...'
    link = 'http://bit.ly/wpidaka'
    max_size = 140 - len(header) + len(elipsis)
    items_listed = ', '.join(items)
    if (len(items_listed) > max_size):
        truncated_items_listed = items_listed[0:max_size]
        truncated_items_listed = truncated_items_listed.rpartition(',')[0]
        truncated_items_listed += elipsis
    else:
        truncated_items_listed = items_listed
    return header + truncated_items_listed
    

def post_msg_to_twitter(msg):
    consumer_key = os.environ.get('DAKA_CONSUMER_KEY')
    consumer_secret = os.environ.get('DAKA_CONSUMER_SECRET')
    access_token = os.environ.get('DAKA_ACCESS_TOKEN')
    access_token_secret = os.environ.get('DAKA_ACCESS_TOKEN_SECRET')

    api = twitter.Api(consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=access_token,
                      access_token_secret=access_token_secret)

    api.PostUpdate(msg)    

if __name__=="__main__":
    options = get_command_line_options()
    todays_date = date.today().strftime('%m/%d/%y')
    menu_html = request_todays_menu_html(todays_date)
    soup = BeautifulSoup(menu_html)
    if options.meal == 'breakfast':
        items = find_breakfast_items(soup)
    elif options.meal == 'lunch':
        items = find_lunch_items(soup)
    elif options.meal == 'dinner':
        items = find_dinner_items(soup)
    
    msg = format_items_message(items)
    
    print msg
    
