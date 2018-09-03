import csv
import functools
import queue
import re
import threading
from time import time
import requests
from bs4 import BeautifulSoup
import os

import ipProcess.ip as ip
import gloSetting as gl


# 获取函数运行时间装饰器
def excute_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        spend = time() - start
        print('%s() 运行时间: %d' % (func.__name__, spend))
        #         thread_num = ''
        #         if 'thread_num' in kwargs:
        #             thread_num = kwargs['thread_num']

        #         # 运行时间写入文件
        #         headers = ['函数', '运行时间', '线程数']
        #         if os.path.isfile('运行时间统计.csv'):
        #             with open('运行时间统计.csv', 'a', newline='') as f:
        #                 writer = csv.DictWriter(f, headers)
        #                 data = {'函数':func.__name__, '运行时间':spend, '线程数':thread_num}
        #                 writer.writerow(data)
        #         else:
        #             with open('运行时间统计.csv', 'a', newline='') as f:
        #                 writer = csv.DictWriter(f, headers)
        #                 writer.writeheader()
        #                 data = {'函数':func.__name__, '运行时间':spend, '线程数':thread_num}
        #                 writer.writerow(data)

        return result

    return wrapper


@excute_time
def put_job_object_queue(url):
    proxy = gl.proxy
    job_object_queue = gl.job_object_queue

    flag = True

    # TODO 查看信息
    print('put_job_object_queue()当前处理链接:', url)
    while flag:
        try:
            r = requests.get(url, proxies=proxy, timeout=5)
            # 报了异常的话捕捉了之后
            # 获得新的proxy之后就直接开始下次循环
        except requests.RequestException as e:
            print(e)
            proxy = ip.get_proxy()
            print('尝试新的proxy')
            continue

        # 不报异常就取消循环
        flag = False

    r.encoding = 'gbk'
    html = r.text
    soup = BeautifulSoup(html, features='html5lib')
    # 找到了工作列表的开头
    title = soup.find('div', 'el title')
    # 找到每一个工作列，它们分别是一个div class='el'
    job_info_list = title.find_next_siblings('div', 'el')

    # 存放当前页jobObject对象到job_object_queue中
    for tag in job_info_list:
        object = gl.job_object()
        object.tag_href = tag.find('a').attrs['href']
        object.job = tag.find('a').attrs['title']

        infos = tag.find_all(class_=re.compile('t[2-4]'))
        object.company = infos[0].string
        object.address = infos[1].string
        object.salary = infos[2].string
        job_object_queue.put(object)

    print('put_job_object_queue()处理完成!')


@excute_time
def get_tag(url):
    proxy = gl.proxy
    tag_url = url

    # 存储标签的List
    tag_list = []
    flag = True

    # TODO 查看信息
    print(threading.current_thread().getName() + ' getTag()当前处理链接:', tag_url)
    print('getTag()获得的ip:', proxy)
    while flag:
        # headers = {'user-agent','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.181 Chrome/66.0.3359.181 Safari/537.36'}
        try:
            r_tag = requests.get(tag_url, timeout=5, proxies=proxy)

        # 报了异常的话捕捉了之后
        # 获得新的proxy之后就直接开始下次循环
        except requests.RequestException as e:
            print(e)
            proxy = ip.get_proxy()
            print('尝试新的proxy')
            continue

        flag = False

    r_tag.encoding = 'gbk'
    tag_html = r_tag.text
    tag_soup = BeautifulSoup(tag_html, features='html5lib')

    # 找到详情页第一行标签
    tag_1_list = []
    tag = tag_soup.find_all('span', 'sp4')
    if tag is not None:
        for i in tag:
            tag_1_list.append(i.contents)
    tag_list.append(tag_1_list)

    # 找到详情页第二行标签
    tag_2_list = tag_soup.find('p', 'msg ltype')
    if tag_2_list is not None:
        tag_2_list = tag_2_list['title'].split()
        tag_2_list = [tag for tag in tag_2_list if tag != '|']

    tag_list.append(tag_2_list)

    print('getTag()中tag_list:', tag_list)
    print('----------------------')

    return tag_list


@excute_time
def pack_tag(**thread_num):
    job_object_queue = gl.job_object_queue

    final_job_object_queue = queue.Queue()

    def pack_object():
        while True:
            print('job_object_queue的大小: ', job_object_queue.qsize())
            jobObject = job_object_queue.get()
            jobObject.tag = get_tag(jobObject.tag_href)
            final_job_object_queue.put(jobObject)
            #             if job_object_queue.qsize() == 0:
            #                 flag =False
            job_object_queue.task_done()

    threads = []

    for i in range(thread_num.get('thread_num')):
        thread = threading.Thread(target=pack_object)
        thread.setDaemon(True)
        threads.append(thread)
        thread.start()

    job_object_queue.join()

    #     pack_object()
    print('tag组装完成!')
    return final_job_object_queue


def save_job_object_queue_to_csv(final_job_object_queue):
    headers = ['职位', '公司', '地址', '薪酬', '标签']
    datas = []

    flag = True

    while flag:
        job_object = final_job_object_queue.get()
        data = {headers[0]: job_object.job,
                headers[1]: job_object.company,
                headers[2]: job_object.address,
                headers[3]: job_object.salary,
                headers[4]: job_object.tag}
        datas.append(data)
        if final_job_object_queue.qsize() == 0:
            flag = False

    if os.path.isfile('51job.csv'):
        with open('51job.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, headers)
            for row in datas:
                writer.writerow(row)
    else:
        with open('51job.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, headers)
            writer.writeheader()
            for row in datas:
                writer.writerow(row)


def handle_page_to_job_object_queue(pages, thread_nums):
    proxy = gl.proxy
    job_object_queue = gl.job_object_queue
    url_queue = queue.Queue()

    # 生成url的queue
    for i in range(pages):
        url = 'https://search.51job.com/list/000000,000000,0000,00,9,99,Java,2,{}.html?lang=c&stype=&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&providesalary=99&lonlat=0%2C0&radius=-1&ord_field=0&confirmdate=9&fromType=&dibiaoid=0&address=&line=&specialarea=00&from=&welfare=' \
            .format(i + 1)
        url_queue.put(url)

    # 每个线程读取链接，分析该页的job_object,放到job_object_queue中
    def go(url_queue, proxy):
        flag = True
        while flag:
            url = url_queue.get()
            put_job_object_queue(url)

            if url_queue.qsize() == 0:
                flag = False

    threads = []

    for i in range(thread_nums):
        thread = threading.Thread(target=go, args=(url_queue, proxy))
        threads.append(thread)

    start = time()
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    result = time() - start
    print('爬取时间:', result)
