#!/usr/bin/env python3

"""
The Pirate Bay utility

Usage:
  tpb [--verbose] [--mirror=<mirror>] [--category=<category>] [--limit=<limit>] search <term>
  tpb [--verbose] [--mirror=<mirror>] [--category=<category>] download <term>
  tpb [--verbose] [--mirror=<mirror>] --list-categories
  tpb [--verbose] configure --mirror=<mirror>
  tpb [--verbose] show
  tpb [--verbose] status

Options:
  --verbose     Verbose mode
"""

import sys
import os
import json
import re
import subprocess
import urllib.parse
from pprint import pprint
import requests
from docopt import docopt
from bs4 import BeautifulSoup

__APPNAME__ = "tpb"

def extract_date(date_string):
    """ return hard coded string for now """
    print(date_string)

class TPB:
    """ TPB class """
    NORMAL = '\033[0m'     # normal
    RED = '\033[1;31m'     # red
    GREEN = '\033[1;32m'   # green
    YELLOW = '\033[1;33m'  # yellow
    BLUE = '\033[1;34m'    # blue
    PURPLE = '\033[35m'    # purple
    MAGENTA = '\033[1;35m' # magenta

    SEARCH = "/search.php"
    HEADERS = {
        "User-Agent": "tbp browser/0.1"
    }

    def __init__(self, verbose):
        """ Constructor """
        self.verbose = verbose
        self.title = ""
        self.link = ""
        self.seeders = ""
        self.leechers = ""
        self.size = ""
        if os.name == "posix":
            self.configpath = os.path.join(os.environ['HOME'],
                                           ".config/{}.json".format(__APPNAME__))
            self.downloader = 'aria2c'
        else:
            print("ERROR Unsupported platform")
            sys.exit(1)
        if os.path.exists(self.configpath):
            if not os.path.isfile(self.configpath):
                print("{} is not a regular file. Please remove and try again." %
                      self.configpath)
            else:
                with open(self.configpath, 'r') as fp:
                    self.config = json.load(fp)
                    if verbose:
                        print("Loading configuration from %s" % self.configpath)
                        pprint(self.config)
                    fp.close()
        else:
            basedir = os.path.dirname(self.configpath)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            with open(self.config, 'w') as fp:
                fp.close()

    def configure(self, mirror):
        """ Configure tpb with the given mirror """
        if self.verbose:
            print("Configuring {} with {} mirror".format(__APPNAME__, mirror))
        configuration = {'mirror': mirror}
        with open(self.configpath, 'w') as cfg:
            json.dump(configuration, cfg, indent=4)
            cfg.close()

    def show(self):
        """ Show tpb mirror settings """
        print(json.dumps(self.config, indent=4, sort_keys=True))

    def top(self, mirror, category):
        """ Show top results for the search term """
        if self.verbose:
            print("Top results for {} @{}".format(category, mirror))

    def download(self, mirror, term):
        """ Download the top result """
        if self.verbose:
            print("Downloading {} {} ({} SE/{} LE)".format(str(self.title),
                                                           self.size, self.seeders, self.leechers))
        self.search(mirror, 1, term)
        print("{} {}".format(self.downloader, self.link))
        subprocess.call([self.downloader, self.link])

    def search(self, mirror, limitstr, term):
        """ Search the site for the term """
        if mirror is None:
            mirror = self.config['mirror']
        if limitstr is None:
            limit = 10
        else:
            limit = int(limitstr)
        if self.verbose:
            print("Searching {} @{}".format(term, mirror))
        params = {'q': term}
        url = "https://{}{}?{}".format(mirror, self.SEARCH,
                                       urllib.parse.urlencode(params))
        if self.verbose:
            print(url)
        res = requests.get(url, headers=self.HEADERS)
        if res.status_code != requests.codes.ok:
            print("{}".format(requests.status_codes._codes[res.status_code][0]))
            return False
        if self.verbose:
            with open('{}.html'.format(term), 'w') as fp:
                fp.write(res.text)
                fp.close()
        soup = BeautifulSoup(res.text, 'html.parser')
        for div in soup.find_all('div', attrs={'class': 'detName'}, limit=limit):
            try:
                div.parent.contents[1].text.encode('utf-8')
                self.title = div.parent.contents[1].text.strip().rstrip()
            except UnicodeError:
                self.title = div.parent.contents[1].strip().rstrip()
            self.link = div.parent.contents[3]['href']
            if hasattr(div.parent.contents[8], 'text'):
                sizestr = div.parent.contents[8].text
            elif hasattr(div.parent.contents[7], 'text'):
                sizestr = div.parent.contents[7].text
            else:
                print("Can't find size: {}".format(div))
            m = re.search("Size [^,]*", str(sizestr.encode('utf-8')))
            self.size = m.group(0).replace('\\xc2', '').replace('\\xa0', '')
            seeders = div.parent.findNext('td')
            self.leechers = seeders.findNext('td').text
            self.seeders = seeders.text
            print("{} ({}, SE {}, LE {})".format(self.title, self.size,
                                                 self.seeders, self.leechers))

    def status(self):
        """ Show status of various proxybay sites """
        proxybayone = "https://proxybay.one"
        res = requests.get(proxybayone, headers=self.HEADERS)
        if res.status_code != requests.codes.ok:
            print("{}".format(requests.status_codes._codes[res.status_code][0]))
            return False
        soup = BeautifulSoup(res.text, 'html.parser')
        for tmp in soup.select('script'):
            offset = str(tmp).find('statusDate')
            if offset > 0:
                datestr = str(tmp)[offset + len("statusDate').innerHTML='"):-len("';</script>")]
                print(datestr)
        sites = soup.find('table', id='searchResult')
        rows = sites.find_all('tr')
        for row in rows:
            site = row.find('a', attrs={'class': 't1'})
            if site:
                _speed = row.find('td', attrs={'class': 'speed'})
                if _speed.string == 'N/A':
                    status = self.RED + _speed.string + self.NORMAL
                else:
                    speed = float(_speed.string)
                    if speed < 1.5:
                        status = self.MAGENTA + "Very Fast" + self.NORMAL
                    elif speed > 1.5 and speed < 2.5:
                        status = self.PURPLE + "Fast" + self.NORMAL
                    elif speed > 2.5 and speed < 5.0:
                        status = self.YELLOW + "Average" + self.NORMAL
                    elif speed > 5.0:
                        status = self.RED + "Slow" + self.NORMAL
                print("{:30s} {}".format(site.string, status))

        return True

if __name__ == "__main__":
    args = docopt(__doc__)
    tpb = TPB(args["--verbose"])
    if args["status"]:
        sys.exit(0 if tpb.status() else 1)

    if args["configure"]:
        tpb.configure(args["--mirror"])
    elif args["search"]:
        tpb.search(args["--mirror"], args["--limit"], args["<term>"])
    elif args["download"]:
        tpb.download(args["--mirror"], args["<term>"])
    elif args["show"]:
        tpb.show()
    else:
        print("Operation not supported.")
