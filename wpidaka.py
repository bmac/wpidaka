from datetime import date
import requests
from BeautifulSoup import BeautifulSoup


def requestTodaysMenuHtml(date):
    payload = {'dt': date, 'venueName': 'Pulse On Dining Marketplace'}
    r = requests.get("http://www.dineoncampus.com/wpi/webtrition/webtrition.cfm", params=payload)
    # r = requests.post("http://localhost:8000", params=payload)
    return r.text



MENU_TABLE_CLASS = 'menu-content'
BREAKFAST_TABLE_ID = 'menu-tbl-1'
AFTERNOON_SNACK_TABLE_ID = 'menu-tbl-2'
LUNCH_TABLE_ID = 'menu-tbl-3'
DINNER_TABLE_ID = 'menu-tbl-4'
LATE_NIGHT_TABLE_ID = 'menu-tbl-5'


def findBreakfastItems(soup):
    breakfast_table = soup.find(id=BREAKFAST_TABLE_ID)
    items = breakfast_table.findAll('span', 'item-name')
    items_text = [i.text for i in items]
    return items_text

def formatItemsMessage(items):
    header = 'Daka is now serving '
    elipsis = '...'
    items_listed = ', '.join(items)
    if (len(items_listed) > 117):
        truncated_items_listed = items_listed[0:117]
        truncated_items_listed = truncated_items_listed.rpartition(',')[0]
    else:
        truncated_items_listed = items_listed
    return header + truncated_items_listed + elipsis
    

if __name__=="__main__":    
    todaysDate = date.today().strftime('%m/%d/%y')
    menu_html = requestTodaysMenuHtml(todaysDate)
    breakfast_items = findBreakfastItems(BeautifulSoup(menu_html))
    print formatItemsMessage(breakfast_items)
