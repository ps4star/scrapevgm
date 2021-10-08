import requests
from bs4 import BeautifulSoup
import sys
import os
import _thread as thread
import threading
import time
from datetime import datetime

MAX_THREADS = 8

def clr_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def mkdir(name):
    try:
        os.mkdir(name)
        print("MKDIR " + name)
    except Exception as e:
        pass

mkdir('./vgmusic-midis')
mkdir('./vgmusic-midis/newly-submitted')
mkdir('./vgmusic-midis/archive')

print("Imports & dir setup successful")

headers = { "Accept-Language": "en-US, en;q=0.5" }

gfnum = 0
def get_mid(base_path, link, location, num_pages, this_idx):
    global gfnum
    link_href = link.get('href')
    if link_href == None:
        gfnum += 1
        return

    # Replace % codes in url
    try:
        while link_href.index("%") > -1:
            idx = link_href.index("%")
            char = chr(int(link_href[idx + 1] + link_href[idx + 2], 16))

            link_href = link_href[:idx] + char + link_href[(idx + 3):]
    except Exception as e:
        pass

    file_ext = link_href.split('.')[-1]
    file_name = link_href.split('/')[-1]

    if num_pages != False:
        # Prepend num (so no dupes can happen) if newly-submitted only
        file_name = str(this_idx) + "_" + file_name

    # Skip if midi already exists
    if os.path.isfile(base_path + file_name):
        print("SKIP " + file_name + " because it already exists lol.")
        gfnum += 1
        return

    if file_ext == 'mid' or file_ext == 'midi':
        # Download midi
        midi_location = location + file_name
        midi_file = requests.get(midi_location).text
        
        f = open(base_path + file_name, 'w')
        f.write(midi_file)
        f.close()

        if num_pages != False:
            print("SUCCESS wrote newly-submitted " + file_name + " | " + str( gfnum / ( num_pages * 100 ) * 100)[:4] + "%")
        else:
            print("SUCCESS wrote archive " + file_name)
    
    gfnum += 1
    return


if sys.argv[1] == "newly-submitted" or sys.argv[1] == "all":
    print("INFO grabbing newly submitted files from vgmusic")

    location = "http://vgmusic.com/new-files/"
    html = requests.get(location)
    soup = BeautifulSoup(html.text, "html.parser")

    this_num = -1

    # Gets num of pages
    base_path = "./vgmusic-midis/newly-submitted/"
    all_forms = soup.find_all('form')
    num_pages = -1
    for form in all_forms:
        if form.get('action') == '/new-files/index.php':
            num_pages += 1
    
    print('INFO need to grab ' + str(num_pages) + ' pages of midis.')
    print('That\'s approximately ' + str(num_pages * 100) + ' midi files in total.')
    fnum = 0
    for i in range(num_pages):
        page_num = str(i + 1)
        soup2 = BeautifulSoup(requests.get(location + "index.php?page=" + str(page_num) + "&s1=date&sd1=1").text, "html.parser")
        all_as = soup2.find_all("a")
        all_as_len = len(all_as)
        j = 0
        while j < all_as_len:
            if j + MAX_THREADS >= all_as_len:
                # Single-threaded
                this_num += 1
                link = all_as[j]
                get_mid(base_path, link, location, num_pages, (this_num -1) // 2)
                j += 1
            else:
                # Multi-threaded
                t = None
                for k in range(MAX_THREADS):
                    this_num += 1
                    link = all_as[j + k]
                    t = threading.Thread( target=get_mid, args=(base_path, link, location, num_pages, (this_num -1) // 2) )
                    t.start()
                    time.sleep(0.01)

                while t.is_alive():
                    time.sleep(0.01)

                j += MAX_THREADS

if sys.argv[1] == "archive" or sys.argv[1] == "all":
    print("INFO grabbing archive files from vgmusic")

    # Grab archive
    location = "http://vgmusic.com/"
    html = requests.get(location)
    soup = BeautifulSoup(html.text, "html.parser")
    base_path = "./vgmusic-midis/archive/"

    this_num = -1

    # Get console links
    possible_links = soup.find_all('option')
    for link in possible_links:
        # Only a valid console link if has 'music/console' in url
        url = link.get('value')
        if "music/console" in url:
            # Valid console url
            this_console_name = (url[:-1] if url[-1] == '/' else url).split('/')[-1]

            cons_soup = BeautifulSoup(requests.get(url).text, "html.parser")
            all_as = cons_soup.find_all('a')
            all_as_len = len(all_as)
            j = 0

            while j < all_as_len:
                final_path = base_path + this_console_name + "/"
                mkdir(final_path)
                if j + MAX_THREADS >= all_as_len:
                    # Single-threaded
                    this_num += 1
                    link = all_as[j]
                    get_mid(final_path, link, url, False, (this_num -1) // 2)
                    j += 1
                else:
                    # Multi-threaded
                    t = None
                    for k in range(MAX_THREADS):
                        this_num += 1
                        link = all_as[j + k]

                        t = threading.Thread( target=get_mid, args=(final_path, link, url, False, (this_num -1) // 2) )
                        t.start()
                        time.sleep(0.01)

                    while t.is_alive():
                        time.sleep(0.01)

                    j += MAX_THREADS