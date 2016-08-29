import get_forum_list
import get_single_thread
from selenium import webdriver
from urllib.parse import unquote
import os
import shutil
import signal
import json
from datetime import datetime
from bs4 import BeautifulSoup


def get_forum_list_call(url):
    get_forum_list.browser = webdriver.PhantomJS()
    get_forum_list.get_forum_list(url)
    get_forum_list.browser.service.process.send_signal(signal.SIGTERM)
    get_forum_list.browser.quit()


def kill_fake_thread(page_path, page, tid):
    with open(page_path, 'r', encoding='utf8') as f:
        html_tree = BeautifulSoup(f, 'lxml')
    target_node = html_tree.find('a', href=str(page) + '_thread/' + tid + '/1.html')
    if target_node:
        for parent in target_node.parents:
            try:
                if 'j_thread_list' in parent['class']:
                    print('found you!')
                    parent.decompose()
                    found = True
                    break
            except BaseException:
                print('continue find!')
        if found:
            os.remove(page_path)
            with open(page_path, 'w', encoding='utf8') as f:
                f.write(str(html_tree))
            print('kill success!')
        else:
            print('!!!--error--!!! kill fail')
    else:
        print('!!!--error--!!! kill fail')


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
                            has_fake_thread = get_single_thread.get_single_thread(tid, fid, info['title'])
                            if has_fake_thread:
                                kill_fake_thread(info_file_name + '/' + str(page) + '.html', page, tid)
                            else:
                                shutil.copytree(tid, info_file_name + '/' + str(page) + '_thread/' + tid)
                                shutil.rmtree(tid)
                        except BaseException:
                            print('!!!--error--!!! download error tid:' + tid)


if __name__ == '__main__':
    my_cookie = "BAIDUID=1EA1D52D7B28CC07BE2DF39ADF37CCDA:FG=1; TIEBA_USERTYPE=e7d5aa4ed3bd6481d6d4934a; bdshare_firstime=1471439905469; PSTM=1471440014; BIDUPSID=1EA1D52D7B28CC07BE2DF39ADF37CCDA; IS_NEW_USER=aa1333218b3ff02296140f74; CLIENTWIDTH=550; CLIENTHEIGHT=1879; app_open=1; bdps_login_cookie=1; pb_prompt=1; SEENKW=iur_li; SET_PB_IMAGE_WIDTH=436; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; BDUSS=pwdE42azRNam9oaGZwckNJR1E5d1pCUUxvSVZOa2p-VjJmUHVpR3hBeEk3ZHhYQVFBQUFBJCQAAAAAAAAAAAEAAAAJHzMmxOrEt8Cty7kAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEhgtVdIYLVXSX; H_PS_PSSID=20742_1469_18280_17949_18133_17001_11536_20697_20857_20836_20771_20781; TIEBAUID=e7d5aa4e52fee3f0d6d493bb; LONGID=640884489; wise_device=0;"
    my_url = "http://tieba.baidu.com/f?ie=utf-8&kw=%E6%9D%B0%E9%92%A2%E9%98%9F%E9%95%BF"
    print(datetime.now())
    # get_forum_list_call(my_url)
    get_threads_from_forum_page(my_url, my_cookie)
    print(datetime.now())
