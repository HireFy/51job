import queue
from time import time
import requests
from bs4 import BeautifulSoup
import threading
import gloSetting as gl


def ip_to_queue():
    q = queue.Queue()
    url = gl.url_proxy
    while (True):
        try:
            r = requests.get(url, timeout=5)
        except Exception as e:
            print(e)
            continue
        break
    html = r.text
    soup = BeautifulSoup(html, features='html5lib')
    all_p = soup.find_all('p')
    for ip in all_p:
        q.put(ip.string.split('\'')[3])

    return q


# 把存有ip的queue格式化成requests的proxy接受的形式
def get_proxy_style():
    ip_queue = ip_to_queue()
    proxies = queue.Queue()

    flag = True
    while flag:
        ip = ip_queue.get()
        proxy = {'http': ip, 'https': ip}
        proxies.put(proxy)
        if ip_queue.qsize() == 0:
            flag = False

    return proxies


def get_clean_proxies(proxies, **thread_num):
    url = gl.url_to_check
    # 有效的ip队列
    ok_proxies = queue.Queue()

    def check_proxy():

        proxies_size = proxies.qsize()
        while True:
            proxies_size = proxies.qsize()
            print('%s : 当前剩余处理的ip: %d' % (threading.current_thread().name, proxies_size))

            proxy = proxies.get()
            try:
                r = requests.get(url, proxies=proxy, timeout=5)
                print(threading.current_thread().name + ' is processing')
                print('r.status_code:', r.status_code)
                if (r.status_code != 200):
                    print('remove proxy:', proxy)
                else:
                    ok_proxies.put(proxy)

                proxies.task_done()
                print('-------------------------------------')
            except requests.RequestException as e:
                proxies.task_done()
                print(threading.current_thread().name + ' is processing')
                print(e)
                print('remove proxy:', proxy)
                print('-------------------------------------')

    threads = []

    for i in range(thread_num.get('thread_num')):
        thread = threading.Thread(target=check_proxy)
        thread.setDaemon(True)
        threads.append(thread)
        thread.start()

    proxies.join()

    return ok_proxies


# 获取proxy
# 当队列中的proxy用完了的时候在获取新的proxies
# 不是每次线程启动就获取新的proxies
# 当一个proxy不能用了才能获取新的proxy
def get_proxy():
    gl.lock.acquire()
    if gl.proxies.qsize() == 0:
        proxies = get_proxies()
    gl.lock.release()
    return gl.proxies.get()


def get_proxies():
    # 多线程的话，就不保存在本地文件
    # 应该保存在各自线程的queue里面
    ip_start = time()
    gl.proxies = get_proxy_style()
    gl.proxies = get_clean_proxies(gl.proxies, thread_num=300)
    ip_cost_time = time() - ip_start
    print('可用的ip: ', gl.proxies.qsize())
    print('%s清洗ip的时间: %d' % (threading.current_thread().name, ip_cost_time))
    return gl.proxies