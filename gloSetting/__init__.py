import threading
import queue

# 全局变量
lock = threading.Lock()
job_object_queue = queue.Queue()
proxies = queue.Queue()
proxy = {}


class job_object:
    'job描述对象'
    __slots__ = ('tag_href', "job", 'company', 'address', 'salary', 'tag')
