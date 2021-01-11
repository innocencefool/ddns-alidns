#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import logging
import os
import time

from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkcore.client import AcsClient

# pip3 install aliyun-python-sdk-alidns -i https://mirrors.aliyun.com/pypi/simple

ACCESSKEY_ID = '########################'
ACCESSKEY_SECRET = '##############################'
DOMAIN = 'alidns.com'
RECORD = 'www'

TURN = {'00:00:00': 'jp.alidns.com', '18:00:00': 'us.alidns.com'}

SUBDOMAIN = '%s.%s' % (RECORD, DOMAIN)

DDNS_CONF = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'ddns-alidns-turn.conf'
DDNS_LOG = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'ddns-alidns-turn.log'

acsClient = AcsClient(ACCESSKEY_ID, ACCESSKEY_SECRET, 'cn-hangzhou')


def load_conf():
    try:
        if not os.path.exists(DDNS_CONF):
            save_conf()
        with open(DDNS_CONF, 'r') as ddns_conf:
            dict_conf = json.load(ddns_conf)
            if dict_conf.get('subdomain') is not None and dict_conf.get('subdomain') == SUBDOMAIN:
                return dict_conf.get('record_id')
    except Exception as e:
        logging.error(e)


def save_conf():
    try:
        dict_conf = {'subdomain': SUBDOMAIN, 'record_id': describe_records(False)}
        with open(DDNS_CONF, 'w') as ddns_conf:
            json.dump(dict_conf, ddns_conf)
    except Exception as e:
        logging.error(e)


def describe_records(value=True):
    try:
        logging.info('DescribeSubDomainRecordsRequest %s' % SUBDOMAIN)
        request = DescribeSubDomainRecordsRequest()
        request.set_DomainName(DOMAIN)
        request.set_SubDomain(SUBDOMAIN)
        request.set_Type('CNAME')
        request.set_Line('default')
        request.set_accept_format('json')
        response = acsClient.do_action_with_exception(request)
        if value:
            return json.loads(response)['DomainRecords']['Record'][0]['Value']
        else:
            return json.loads(response)['DomainRecords']['Record'][0]['RecordId']
    except Exception as e:
        logging.error(e)


def update_record(record_id, value):
    try:
        logging.info('UpdateDomainRecordRequest %s %s' % (SUBDOMAIN, value))
        request = UpdateDomainRecordRequest()
        request.set_RecordId(record_id)
        request.set_RR(RECORD)
        request.set_Type('CNAME')
        request.set_Line('default')
        request.set_Value(value)
        request.set_accept_format('json')
        response = acsClient.do_action_with_exception(request)
        return json.loads(response)['RecordId']
    except Exception as e:
        logging.error(e)


def my_turn():
    now = time.strftime("%H:%M:%S", time.localtime())
    keys = sorted(TURN.keys())
    value = None
    for key in keys:
        if now >= key:
            value = TURN.get(key)
        elif value is None:
            value = TURN.get(keys[-1])
    return value


def main():
    record_id = load_conf()
    if record_id is not None:
        recorded = describe_records()
        if recorded is not None:
            expected = my_turn()
            if expected is not None and expected != recorded:
                update_record(record_id, expected)


if __name__ == '__main__':
    logging.basicConfig(filename=DDNS_LOG, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    main()
