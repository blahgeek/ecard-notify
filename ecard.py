#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by i@BlahGeek.com at 2015-04-04

from collections import namedtuple
from datetime import datetime
import re
import logging
import requests
from bs4 import BeautifulSoup
import xml.sax.saxutils as saxutils

sess = requests.session()

Record = namedtuple('Record', ['location', 'type_', 'date', 'amount'])

def get_ecard_url(username, password):
    sess.post('https://info.tsinghua.edu.cn/Login', {
                  'redirect': 'NO',
                  'x': 0, 'y': 0,
                  'userName': username,
                  'password': password
              })
    req = sess.get('http://info.tsinghua.edu.cn/render.userLayoutRootNode.uP')
    url = re.search(r'"(http://ecard\.tsinghua\.edu\.cn/user/Login\.do.+)"', req.text).group(1)
    url = saxutils.unescape(url)
    logging.info('Got ecard url: %s' % url)
    return url

def get_result(url):
    req = sess.get(url)
    soup = BeautifulSoup(req.content)
    table = soup.form.div.findChild('table', recursive=False)
    trs = table.findAll('tr', recursive=False)[1:]
    result = map(lambda tr: [td.text.strip() for td in tr.findAll('td')], trs)
    return map(lambda x: Record(x[0], x[1], datetime(*map(int, x[2].split('-'))), float(x[3].strip(u'￥'))), result)
