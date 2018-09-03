import threading
import queue

# 全局变量
lock = threading.Lock()
job_object_queue = queue.Queue()
proxies = queue.Queue()
proxy = {}
url_to_check = 'https://jobs.51job.com/'
url_proxy = 'http://45.76.218.205:8000'


class job_object:
    'job描述对象'
    __slots__ = ('tag_href', "job", 'company', 'address', 'salary', 'tag')
