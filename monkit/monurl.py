#!/usr/bin/env python
# coding: utf-8
import os
import time
import sys
import re
import StringIO
import pycurl
import requests
import urllib
import json
import threading
import socket


def monpush(metric, value, tags=''):
    furl = 'http://127.0.0.1:2058/api/collector/push'
    step = 60
    payload = [{'metric':metric, 'timestamp':int(time.time()), 'step':step, 'value':value, 'tags':tags}]
    headers = {'Content-Type': 'application/json'}
    ret = requests.post(furl, data=json.dumps(payload), headers=headers, timeout=5)
    return ret.text

def request_get(url, timeout=5, headers=None):
    import re
    ret = err = None
    try:
        import requests
    except Exception as e:
        return ret, e
    if not re.match('https?://',url.strip()): url = 'http://' + url
    try:
        ret = requests.get(url, timeout=timeout, headers=headers)
    except Exception as e:
        return ret, e
    return ret, err

def test_web(**kw):
    CONNECTTIMEOUT = 30
    TIMEOUT = 50
    t = StringIO.StringIO()
    api = kw['api']
    method = kw['method']
    post_data= kw['params']
    #cookie = kw['cookie']
    headers = kw['headers']
    expect_httpcode = kw['expect_httpcode']
    expect_string = kw['expect_string']
    timeout = kw['timeout']
    level = kw['level']
    appname = kw.get('appname', '')
    tag = kw['tags']
    tags = 'api={},method={}'.format(api, method)
    if appname: tags = '{},appname={}'.format(tags, appname)
    if tag: tags = '{},{}'.format(tags, tag)
    api = api.encode('gb2312')
    #url = url.encode('gb2312')
    c = pycurl.Curl()
    c.setopt(pycurl.WRITEFUNCTION,t.write)

    c.setopt(pycurl.FOLLOWLOCATION, 1)  #开启跟踪，开启自动跳转
    c.setopt(pycurl.MAXREDIRS, 5) #最大重定向次数,可以预防重定向陷阱
    if method == 'POST':
        post_data = json.dumps(post_data)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, post_data)
    c.setopt(pycurl.URL, api)
    c.setopt(pycurl.NOSIGNAL, 1) #禁用python的信号量，避免libcurl的问题导致程序crash
    if api.startswith('https'):
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)

    c.setopt(pycurl.CONNECTTIMEOUT, CONNECTTIMEOUT) #连接超时
    c.setopt(pycurl.TIMEOUT, TIMEOUT)    #下载超时

    c.setopt(pycurl.REFERER, "Url-Monitor/1.0")
    header_list = []
    #header_list.append('Host:' + str(domain))
    if headers:
        headers = headers.split(',')
        for header in headers:
            header_list.append(str(header))
    # if cookie:
    #     cookie_file = '/opt/cookiedir/' + str(cookie)
    #     c.setopt(pycurl.COOKIEFILE, cookie_file)
    #     c.setopt(pycurl.COOKIEJAR, cookie_file)
    c.setopt(pycurl.HTTPHEADER, header_list)
    try:
        c.perform()
        monpush('url.error', 1, tags)
    except Exception,e:
        c.close()
        if 'timed out' in e[1]:
            monpush('url.timeout_error', -1, tags)
        else:
            monpush('url.error', -1, tags)
        return e
    d = {}
    d['dns_time'] = c.getinfo(pycurl.NAMELOOKUP_TIME)                    #DNS 建连时间
    d['conn_time'] = c.getinfo(pycurl.CONNECT_TIME)                      #TCP/IP 三次握手时间
    d['starttransfer_time'] = c.getinfo(pycurl.STARTTRANSFER_TIME)       #首包时间
    d['total_time'] = c.getinfo(pycurl.TOTAL_TIME)                       #上一请求的总时间
    d['http_code'] = c.getinfo(pycurl.HTTP_CODE)                         #HTTP响应代码
    #d['redirect_count'] = c.getinfo(pycurl.REDIRECT_COUNT)               #重定向次数
    #size_upload = c.getinfo(pycurl.SIZE_UPLOAD)                     #上传字节大小
    d['size_download'] = c.getinfo(pycurl.SIZE_DOWNLOAD)                 #下载字节大小
    #d['header_size'] = c.getinfo(pycurl.HEADER_SIZE)                     #头部大小
    #d['request_size'] = c.getinfo(pycurl.REQUEST_SIZE)                   #请求大小
    #d['content_type'] = c.getinfo(pycurl.CONTENT_TYPE)                   #请求内容类型
    d['speed_download'] = c.getinfo(pycurl.SPEED_DOWNLOAD)                #下载速度
    c.close()                                                      #关闭处理Curl的session

    if level == 1:
        for k,v in d.items():
            monpush('url.' + k, v, tags)
    else:
        monpush('url.http_code', d['http_code'], tags)
        monpush('url.total_time', d['total_time'], tags)

    code_value = timeout_value = 1
    if d['http_code'] != expect_httpcode: code_value = -1
    if d['total_time'] > timeout: timeout_value = -1
    monpush('url.http_code_error', code_value, tags)
    monpush('url.timeout_error', timeout_value, tags)

    string_value = 1
    if expect_string:
        if not re.search(expect_string, unicode(t.getvalue(), 'utf-8')): string_value = -1
        monpush('url.string_error', string_value, tags)

    t.close()
    return code_value, timeout_value, string_value

def main():
    api = sys.argv[1]
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    url = '{}?task_type=api&ip={}'.format(api, ip)
    ret, err = request_get(url)
    thread_count = 100
    getconf_value = 1
    if not err and ret.status_code == 200:
        res = ret.json()
        agent_name = res['agent_name']
        conf_list = res['tasks']
        threads = []
        for conf in conf_list:
            t = threading.Thread(target=test_web, kwargs=conf)
            threads.append(t)
        for t in threads:
            #t.setDaemon(True)
            t.start()
            while True:
                if(len(threading.enumerate()) <= thread_count):
                    break
    else:
        getconf_value = -1

if __name__ == '__main__':
    main()
