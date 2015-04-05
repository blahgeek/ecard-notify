#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by i@BlahGeek.com at 2015-04-05

import ecard
from datetime import datetime
import logging
import requests
from db import Record
from apscheduler.schedulers.blocking import BlockingScheduler
import config

def collect(username, password):
    url = ecard.get_ecard_url(username, password)
    records = ecard.get_result(url)
    logging.info('Found %d records' % len(records))
    exists_records = list(Record.select().order_by(Record.created_date.desc())
                                         .limit(len(records)))
    exists_records += [None, ] * (len(records) - len(exists_records))  # Maybe there's less records in db
    eq = lambda x, y: x is not None and y is not None and all(getattr(x, key) == getattr(x, key) for key in ecard.Record._fields)
    delta = 0
    while delta < len(records):
        if all([eq(records[i+delta], exists_records[i]) for i in range(len(records) - delta)]):
            break
        delta += 1
    logging.info('...%d of them are new to me, insert it' % delta)
    for record in records[:delta][::-1]:  # insert oldest record first
        Record.create(**record.__dict__)


def notify(username, password, phonenumber):
    today = datetime.today()
    records = Record.select().where(Record.date == datetime(today.year, today.month, today.day))
    total_amount = sum(map(lambda x: x.amount, records))
    logging.info('Total amount for today (%s): %.1f' % (today.strftime('%Y-%m-%d'), total_amount))
    requests.get('http://api.smsbao.com/sms', params={
                    'u': username,
                    'p': password,
                    'm': phonenumber,
                    'c': u'今天你的校园卡一共刷了%.1f块钱～' % total_amount
                 })


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    Record.create_table(fail_silently=True)

    scheduler = BlockingScheduler()
    scheduler.add_job(collect, 'interval', (config.USERNAME, config.PASSWORD),
                      seconds=3600*6)  # Check every 6 hours
    scheduler.add_job(notify, 'cron', (config.SMSBAO_USERNAME, config.SMSBAO_PASSWORD, config.SMS_PHONE),
                      hour=15, minute=0)  # Send notification at 15:00:00 every day

    logging.info('Starting scheduler...')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

