import queue
import threading
from time import time
import jobProcess.job as job
import ipProcess.ip as ip
import gloSetting as gl

gl.proxies = ip.get_proxies()
gl.proxy = ip.get_proxy()


def main():
    start = time()
    # 指定线程数爬取指定页数，
    job.handle_page_to_job_object_queue(10, 10)
    print("job_object_queue.qsize(): ", gl.job_object_queue.qsize())

    final_job_object_queue = job.pack_tag(thread_num=200)

    print("final_job_object_queue.qsize() : " + str(final_job_object_queue.qsize()))

    job.save_job_object_queue_to_csv(final_job_object_queue)

    result = time() - start
    print('用时: ', result)

#     # todo 分割运行时间统计
#     with open('运行时间统计.csv', 'a', newline='') as f:
#         headers = ['函数', '运行时间', '线程数']
#         writer = csv.DictWriter(f, headers)
#         data = {'函数':'', '运行时间':'', '线程数':''}
#         writer.writerow(data)


if __name__ == '__main__':
    main()