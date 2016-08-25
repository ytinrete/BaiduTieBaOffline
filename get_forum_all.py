import get_forum_list
import get_single_thread
from selenium import webdriver
from urllib.parse import unquote
import os
import shutil
import signal
import json


def get_forum_list_call(url):
    get_forum_list.browser = webdriver.PhantomJS()
    get_forum_list.get_forum_list(url)
    get_forum_list.browser.service.process.send_signal(signal.SIGTERM)
    get_forum_list.browser.quit()


def get_threads_from_forum_page(url, cookie):
    get_single_thread.cookie = cookie
    info_file_name = unquote(unquote(get_forum_list.get_info_from_query(url, 'kw')))
    if os.path.exists(info_file_name + '/forum_base_info.json'):
        with open(info_file_name + '/forum_base_info.json', 'r', encoding='utf-8') as base_info_file:
            info = json.load(base_info_file)

        for page in range(1, info['total_page'] + 1):
            if os.path.exists(info_file_name + '/' + str(page) + '_thread/tid_info.json'):
                with open(info_file_name + '/' + str(page) + '_thread/tid_info.json', 'r',
                          encoding='utf-8') as thread_info_file:
                    tid_info = json.load(thread_info_file)
                fid = tid_info['fid']
                for tid in tid_info['tid_list']:
                    if not os.path.exists(info_file_name + '/' + str(page) + '_thread/' + tid + '/1.html'):
                        try:
                            print('downloading thread ' + tid + ' in page' + str(page))
                            get_single_thread.get_single_thread(tid, fid)
                            shutil.copytree(tid, info_file_name + '/' + str(page) + '_thread/' + tid)
                            shutil.rmtree(tid)
                        except BaseException:
                            print('download error tid:' + tid)


if __name__ == '__main__':
    my_url = ''
    my_cookie = ''
    get_forum_list_call(my_url)
    get_threads_from_forum_page(my_url, my_cookie)
