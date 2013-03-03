import os
import re
from datetime import date
from optparse import OptionParser
import requests
import twitter
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
    assert(r.status_code is 200) #sanity check
    return r.text



MENU_TABLE_CLASS = 'menu-content'
BREAKFAST_TABLE_ID = 'menu-tbl-1'
AFTERNOON_SNACK_TABLE_ID = 'menu-tbl-2'
LUNCH_TABLE_ID = 'menu-tbl-3'
DINNER_TABLE_ID = 'menu-tbl-4'
LATE_NIGHT_TABLE_ID = 'menu-tbl-5'

# dinner and late night seem to swap between menu-tbl-4 and menu-tbl-5
# this function helps us find the correct dinner id
def find_dinner_id(soup):
    nav_items = soup.find(id='mp-nav-wrapper').findAll(class_="mp-nav")
    for item in nav_items:
        if item.text.lower() == 'dinner':
            number = re.search('(\d)', item['id']).group(0)
            return 'menu-tbl-' + number


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
    if soup.getText().lower().find('breakfast') is -1:
        return []
    breakfast_table = soup.find(id=BREAKFAST_TABLE_ID)
    items = breakfast_table.find_all('span', 'item-name')
    items_text = [i.text.strip() for i in items]
    return items_text

def find_interesting_items(table_soup):
    items = []
    items.extend(grab_two_items(table_soup, 'kitchen'))
    items.extend(grab_two_items(table_soup, 'kitchen grill'))
    items.extend(grab_two_items(table_soup, 'scratch made soup offerings'))
    return items

def grab_two_items(soup, section_header):
    items = soup.find_all('span', class_=['item-name', 'station-name'])
    (start, section_start) = partition(items,
                                          lambda x: x.text.strip().lower() == section_header.lower())
    items_text = [span.text.strip() for span in section_start if 'item-name' in span.attrs['class'] ]
    return items_text[:2]

def find_lunch_items(soup):
    lunch_table = soup.find(id=LUNCH_TABLE_ID)
    return find_interesting_items(lunch_table)

def find_dinner_items(soup):
    dinner_table = soup.find(id=find_dinner_id(soup))
    return find_interesting_items(dinner_table)


def format_items_message(items):
    header = 'Now serving: '
    elipsis = '...'
    link = 'http://bit.ly/wpidaka'
    max_size = 140 - len(header) - len(elipsis)
    items_listed = ', '.join(items)
    if (len(items_listed) > max_size):
        truncated_items_listed = items_listed[:max_size]
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

def main():
    options = get_command_line_options()
    if (not options.meal):
        print 'please supply a meal. Usage python wpidaka.py -m (breakfast|lunch|dinner_'
        return 
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

    if options.verbose:
        print msg

    if options.dry_run:
        return

    assert(len(msg) > 40) # sanity check 
    
    post_msg_to_twitter(msg)


if __name__=="__main__":
    main()
