#!/usr/bin/env python
# get-full-list.py - Output URLS for all TED videos.
# Copyright (C) 2012 Mansour Behabadi <mansour@oxplot.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import re

try:
  from urllib2 import urlopen, Request, HTTPError
except ImportError:
  from urllib.request import urlopen, Request
  from urllib.error import HTTPError

_USERAGENT = 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5)' \
            ' Gecko/2008121622 Ubuntu/8.04 (hardy) Firefox/3.0.5'

url = 'http://www.ted.com/talks/quick-list?sort=date&order=desc&page=%d'
headers = {'User-Agent': _USERAGENT}

page = 1
while True:

  content = urlopen(
    Request(url % page, headers=headers)
  ).read().decode('utf8')

  talks = re.findall(
    r'<tr>.+?<a\s+href="(/talks/[^"]+\.html)">.+?'
    r'<a\s+href="http://download[^"]+">High', content, re.DOTALL)
  
  for t in talks:
    print('http://www.ted.com%s' % t)

  if not re.search(r'>Next &raquo;<', content):
    break

  page += 1

