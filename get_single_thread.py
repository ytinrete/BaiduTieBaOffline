from urllib import request as r
import zlib
import time
import os
import shutil
from bs4 import BeautifulSoup
import json
import hashlib


def req_maker(path):
    if path:
        req = r.Request(path)
        req.add_header("User-Agent",
                       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36")
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
        req.add_header("Accept-Encoding", "gzip, deflate, sdch")
        req.add_header("Accept-Language", "zh-CN,zh;q=0.8,en;q=0.6")
        req.add_header("Cookie", cookie)
        return req
    else:
        return None


def get_response_str(req):
    with r.urlopen(req) as f:
        decompressed_data = zlib.decompress(f.read(), 16 + zlib.MAX_WBITS)
        return str(decompressed_data, "utf-8", errors='replace')


def get_now_str():
    return int(float(time.time()) * 1000)


# 单个帖子页面

# 准备好目录
def prepare_folder(tid):
    try:
        os.makedirs(tid)
    except FileExistsError or OSError:
        print('FileExists or OSError return')
        return
    shutil.copytree('model/res', tid + '/res')


# 把数据填充进去,造一个模版出来
def inflate_detail_model_with_data(base_info):
    with open('model/model_detail.html', 'r', encoding='utf8') as f:
        # parser = etree.HTMLParser()
        html_tree = BeautifulSoup(f, 'lxml')
        # return etree.parse(f.read(), parser=parser)

    meta = html_tree.head.select('meta[furl]')[0]
    meta['furl'] = base_info['meta_furl']
    meta['fname'] = base_info['meta_fname']

    title = html_tree.head.title
    title.clear()
    title.append(base_info['title'])

    card_head_img = html_tree.body.find('img', class_='card_head_img')
    card_head_img['src'] = base_info['card_head_img']

    card_title = html_tree.body.find('div', class_='card_title')

    card_title_fname = card_title.find('a', class_='card_title_fname')
    card_title_fname.clear()
    card_title_fname.append(base_info['card_title_fname'])

    card_menNum = card_title.find('span', class_='card_menNum')
    card_menNum.clear()
    card_menNum.append(base_info['card_menNum'])

    card_infoNum = card_title.find('span', class_='card_infoNum')
    card_infoNum.clear()
    card_infoNum.append(base_info['card_infoNum'])

    return html_tree


def get_thread_basic_info_html(_tid):
    html_str = get_response_str(req_maker('http://tieba.baidu.com/p/' + _tid))
    return BeautifulSoup(html_str, 'lxml')


def get_and_save_src(path, save_path):
    try:
        with r.urlopen(req_maker(path)) as f:
            with open(save_path, 'wb') as wf:
                wf.write(f.read())
    except BaseException:
        print('error on donwload:', path)


def get_thread_basic_info(t_tid, t_fid):
    res = {}
    res['tid'] = t_tid
    res['fid'] = t_fid

    html_tree = get_thread_basic_info_html(t_tid)

    # meta furl 我也不知道这个是拿来干嘛
    meta = html_tree.head.select('meta[furl]')
    res['meta_furl'] = meta[0].furl
    res['meta_fname'] = meta[0].fname

    # 标题
    res['title'] = html_tree.head.title.string.strip()
    # print(res['title'])

    # 贴吧头像部分
    res['card_head_img'] = html_tree.body.find('img', class_='card_head_img')['src']
    # print(res['card_head_img'])

    # 下载贴吧头像文件
    # res['card_head_img_path'] = res['tid'] + '/' + urlparse(res['card_head_img']).path.split('/')[-1]
    # with open(res['card_head_img_path, 'wb') as img_src:
    #     img_src.write(get_src(res['card_head_img))

    card_title = html_tree.body.find('div', class_='card_title')

    # 贴吧名称
    res['card_title_fname'] = card_title.find('a', class_='card_title_fname').string.strip()
    # print(res['card_title_fname'])

    # 关注和帖子数
    res['card_menNum'] = card_title.find('span', class_='card_menNum').string.strip()
    # print(res['card_menNum'])
    res['card_infoNum'] = card_title.find('span', class_='card_infoNum').string.strip()
    # print(res['card_infoNum'])

    # 帖子页数,这个比较关键
    l_reply_num_nods = html_tree.find_all('li', class_='l_reply_num')
    for node in l_reply_num_nods:
        if len(node.contents) > 0:
            spans = node.find_all('span', class_='red')
            if len(spans) == 2:
                res['total_page'] = int(spans[1].string.strip())
    # print(res['total_page'])

    return res


# 实际内容和评论列表
def get_thread_by_page(base_info, page):
    html_str = get_response_str(req_maker('http://tieba.baidu.com/p/' + base_info['tid'] + "?ajax=1&pn=" + str(page)))
    html_tree = BeautifulSoup(html_str, 'lxml')
    content = {}
    content['content'] = html_tree.find('div', id='j_p_postlist')
    # <div id="ajax-content"><div class="p_postlist" id="j_p_postlist">直接换
    content['up'] = html_tree.find('div', id='thread_theme_5')
    # <div id="ajax-up"><div class="p_thread thread_theme_5" id="thread_theme_5">这个得处理一下
    content['down'] = html_tree.find('div', id='ajax-down')
    # <div id="ajax-down"><div class="p_thread thread_theme_7" id="thread_theme_7">这个也得处理一下

    # 评论列表,这个是json格式,目标是知道哪个楼有回复,同时拿到comment_num也就是总回复数
    # http://tieba.baidu.com/p/totalComment?tid=4736198966&fid=738100&pn=2&see_lz=0
    json_str = get_response_str(req_maker('http://tieba.baidu.com/p/totalComment?tid='
                                          + base_info['tid'] + '&fid=' + base_info['fid'] + '&pn=' + str(page)))

    json_data = json.loads(json_str)
    # print(json_data)
    comment_data = {}
    for key in json_data['data']['comment_list']:
        comment_data[key] = json_data['data']['comment_list'][key]['comment_num']

    return content, comment_data


# 回复,这个比较麻烦
def make_reply_block():
    # 这个块区添加到对应的div class="j_lzl_container core_reply_wrapper"内部去
    # 评论放到<ul class="j_lzl_m_w" style="display:">里面
    block_str = '''
    <div class="core_reply_border_top">
    </div>
	<div class="j_lzl_c_b_a core_reply_content">
		<ul class="j_lzl_m_w" style="display:">
        </ul>
		<div class="lzl_editor_container j_lzl_e_c lzl_editor_container_s" style="display:none;">
		</div>
	</div>
	<div class="core_reply_border_bottom"></div>
    '''
    return BeautifulSoup(block_str, 'lxml')


# http://tieba.baidu.com/p/comment?tid=3042881140&pid=50510635824&pn=2,这个一次给10条,不过这里会循环一直到取不到为止
# pid为楼层id

def get_comment_by_floor(tid, pid):
    go_on = True
    page = 1
    res = []
    while go_on:
        go_on = False
        html_str = get_response_str(
            req_maker('http://tieba.baidu.com/p/comment?tid=' + tid + "&pid=" + pid + '&pn=' + str(page)))
        html_tree = BeautifulSoup(html_str, 'lxml')
        page += 1
        li_nodes = html_tree.find_all('li')
        for node in li_nodes:
            for count in range(len(node['class'])):
                if node['class'][count] == 'lzl_single_post':
                    res.append(node)
                    go_on = True
                if node['class'][count] == 'first_no_border':
                    node['class'][count] = ''

    block_tree = make_reply_block()
    block_tree_node = block_tree.find('ul')
    for add_node in res:
        block_tree_node.append(add_node)
    return block_tree


# 获取单个帖子,按页保存,能够哪个页面坏了删掉那一页重新跑就行
def get_single_thread(tid, fid, title_check):
    if tid is None or fid is None:
        print('lacking basic info, can not continue!')
        return

    thread_tid = tid
    thread_fid = fid
    base_dir = thread_tid + '/'

    # 1.准备好目录
    print('1.prepare thread folder')
    prepare_folder(thread_tid)

    # 2.收集帖子基本信息
    print('2.get thread basic info')
    if os.path.exists(base_dir + 'base_info.json'):
        print('2.get thread basic info from json')
        with open(base_dir + 'base_info.json', 'r', encoding='utf-8') as base_info_file:
            info = json.load(base_info_file)

    else:
        print('2.get thread basic info from html')
        info = get_thread_basic_info(thread_tid, thread_fid)
        with open(base_dir + 'base_info.json', 'w', encoding='utf-8') as base_info_file:
            base_info_file.write(json.dumps(info))

    if title_check:
        # 贴吧里面会混入别的贴吧的信息,通过校验title干掉大部分这些恶心的东西
        if info['title'].find(title_check) == -1:
            print("fake thread found!!!")
            shutil.rmtree(thread_tid)
            return True

    # 构造模版,并填充基本数据
    print('3.inflate model with info')
    model = inflate_detail_model_with_data(info)

    print('4.start getting pages')
    for page in range(1, info['total_page'] + 1):  # range(1,a.total_page + 1)

        if not os.path.exists(base_dir + str(page) + '.html'):
            print('getting page:' + str(page))
            # 资源目录
            os.makedirs(base_dir + str(page))
            # 清除模版里的旧数据
            p_postlist = model.find('div', id='j_p_postlist')
            p_postlist.clear()
            thread_theme_5 = model.find('div', id='thread_theme_5')
            thread_theme_5.clear()
            thread_theme_7 = model.find('div', id='thread_theme_7')
            thread_theme_7.clear()

            print('getting page detail ' + str(page))
            # 获取实际内容和评论列表
            content, comment_data = get_thread_by_page(info, page)

            # 列表的实际内容
            post_lists = content['content'].find_all('div', class_='l_post')
            for post in post_lists:
                # 取出post数据
                post_data_node = post.find('div', class_="j_d_post_content")

                if post_data_node:
                    post_data_id = post_data_node['id'].split('_')[-1]
                    post_data_node_comment = post.find('div', class_="j_lzl_container")
                    post_data_node_comment['data-field'] = None
                    post_data_node_comment['style'] = None
                    post_data_node_comment.clear()

                    # 送他礼物
                    share_btn_wrapper = post.find('div', class_="share_btn_wrapper")
                    if share_btn_wrapper:
                        share_btn_wrapper.clear()

                    if comment_data.get(post_data_id):
                        # 有评论
                        block_tree = get_comment_by_floor(thread_tid, post_data_id)
                        post_data_node_comment.append(block_tree)

                    p_postlist.append(post)
                    print('adding a floor ' + str(page))
                else:
                    # 广告!!!
                    print('enconter an ad ' + str(page))

            print('dealing with up index ' + str(page))
            # 头部
            l_thread_info_up = content['up'].find('div', class_='l_thread_info')
            a_nodes_up = l_thread_info_up.find_all('a')
            for a_node in a_nodes_up:
                a_node['href'] = None
                if a_node.string == '首页':
                    a_node['href'] = '1.html'
                elif a_node.string == '尾页':
                    a_node['href'] = str(info['total_page']) + '.html'
                elif a_node.string == '上一页':
                    a_node['href'] = str(page - 1) + '.html'
                elif a_node.string == '下一页':
                    a_node['href'] = str(page + 1) + '.html'
                else:
                    try:
                        num = int(a_node.string)
                        a_node['href'] = str(num) + '.html'
                    except TypeError:
                        print('TypeError:' + a_node.prettify())
                    except ValueError:
                        print('unknow page:' + a_node.string)
            thread_theme_5.append(l_thread_info_up)

            print('dealing with down index ' + str(page))
            # 尾部
            l_thread_info_down = content['down'].find('div', class_='l_thread_info')
            a_nodes_down = l_thread_info_down.find_all('a')
            for a_node in a_nodes_down:
                a_node['href'] = None
                if a_node.string == '首页':
                    a_node['href'] = '1.html'
                elif a_node.string == '尾页':
                    a_node['href'] = str(info['total_page']) + '.html'
                elif a_node.string == '上一页':
                    a_node['href'] = str(page - 1) + '.html'
                elif a_node.string == '下一页':
                    a_node['href'] = str(page + 1) + '.html'
                else:
                    try:
                        num = int(a_node.string)
                        a_node['href'] = str(num) + '.html'
                    except TypeError:
                        print('TypeError:' + a_node.prettify())
                    except ValueError:
                        print('unknow page:' + a_node.string)
            thread_theme_7.append(l_thread_info_down)

            print('clear thread_recommend ad ' + str(page))
            # 又一个广告
            AD2 = model.find('div', class_='thread_recommend')
            if AD2:
                AD2.clear()

            print('clear staff under name ' + str(page))
            # 一个奇怪的样式,会挂在名字底下
            d_pb_icons = model.find('span', class_='d_pb_icons')
            if d_pb_icons:
                d_pb_icons.clear()

            # 处理资源,这里再弄一份是因为model突然搜不到带src的标签,我也不知道为什么,重新构造一份才行
            write_model = BeautifulSoup(str(model), 'lxml')

            src_nodes = write_model.select('img[src]')
            print('dealing with src ' + str(page))
            count = 1
            download_list = {}
            for src_node in src_nodes:
                # 部分头像是用这个加载
                lazy_load = src_node.get('data-tb-lazyload')
                if lazy_load:
                    src_node['src'] = lazy_load
                src_str = src_node['src']
                if src_str.find('http') != -1:
                    if download_list.get(src_str):
                        src_node['src'] = download_list.get(src_str)
                    else:
                        md5 = hashlib.md5()
                        md5.update(src_str.encode('utf-8'))
                        link_path = str(page) + '/' + md5.hexdigest() + '.png'
                        src_node['src'] = link_path
                        get_and_save_src(src_str, base_dir + link_path)
                        print('downloading no.' + str(count) + ' img ' + str(page))
                        count += 1
                        download_list[src_str] = link_path
            download_list.clear()

            # 完成,输出
            with open(base_dir + str(page) + '.html', 'w', encoding='utf8') as f:
                f.write(str(write_model))
            print('done with page ' + str(page))


# 有些地方需要登陆,所以cookie自己想办法弄吧
cookie = None

if __name__ == '__main__':
    pass
    # get_single_thread(None, None)
    # with open('3042881140/1.html', 'r', encoding='utf8') as f:
    #     html_tree = BeautifulSoup(f, 'lxml')
    #
    # src = html_tree.select('img[src]')
    # print(len(src))


    # a = ThreadInfo("4369024003", "3092694")

    # a = ThreadInfo("3042881140", "738100")
    # content, comment_data = get_thread_by_page(a, 2)

    # print(get_comment_by_floor('3042881140', '50510635824'))

    # str2 = '{&quot;author&quot;:{&quot;user_id&quot;:323902072,&quot;user_name&quot;:&quot;iur_li&quot;,&quot;props&quot;:null},&quot;content&quot;:{&quot;post_id&quot;:73907222771,&quot;is_anonym&quot;:false,&quot;forum_id&quot;:3092694,&quot;thread_id&quot;:3977770292,&quot;content&quot;:&quot;\u60f3\u4e86\u597d\u4e45\u60e9\u7f5a\u65b9\u5f0f\uff0c\u8fd9\u662f\u4e2a\u5934\u75bc\u7684\u95ee\u9898\uff0c\u672c\u738b\u5bf9\u7269\u8d28\u751f\u6d3b\u8981\u6c42\u8fc7\u4f4e\u4ee5\u81f3\u4e8e\u6ca1\u6709\u4ec0\u4e48\u770b\u8d77\u6765\u80fd\u591f\u8ba9\u6211\u89c9\u5f97\u5fc3\u75bc\u7684\u3002&lt;br&gt;\u60f3\u4e86\u534a\u5929\u7ec8\u4e8e\u60f3\u5230\u4e86\uff0c\u8fdd\u80cc\u672c\u738b\u4ef7\u503c\u89c2\u7684\u76f8\u5f53\u5192\u9669\u7684\u884c\u4e3a\uff0c\u8fd9\u6837\u624d\u523a\u6fc0\u561b\u3002&lt;img class=\&quot;BDE_Smiley\&quot; pic_type=\&quot;1\&quot; width=\&quot;30\&quot; height=\&quot;30\&quot; src=\&quot;http:\/\/tb2.bdstatic.com\/tb\/editor\/images\/face\/i_f25.png?t=20140803\&quot; &gt;&lt;br&gt;\u9664\u7279\u6b8a\u60c5\u51b5\u5916\uff0c\u6ca1\u6709\u4e56\u4e56\u65e9\u8d77\u65e9\u7761\u7684\uff0c\u4e00\u6b21\u7f5a200\uff0c\u6bcf\u5468\u7ed3\u7b97\uff0c\u94b1\u62ff\u53bb\u7092\u80a1&lt;img class=\&quot;BDE_Smiley\&quot; pic_type=\&quot;1\&quot; width=\&quot;30\&quot; height=\&quot;30\&quot; src=\&quot;http:\/\/tb2.bdstatic.com\/tb\/editor\/images\/face\/i_f23.png?t=20140803\&quot; &gt;&lt;br&gt;\u672c\u5468\u7b97\u8bd5\u884c\u5468\uff0c\u7f5a50\uff0c\u4e0b\u5468\u5f00\u59cb200&lt;img class=\&quot;BDE_Smiley\&quot; pic_type=\&quot;1\&quot; width=\&quot;30\&quot; height=\&quot;30\&quot; src=\&quot;http:\/\/tb2.bdstatic.com\/tb\/editor\/images\/face\/i_f25.png?t=20140803\&quot; &gt;&quot;,&quot;post_no&quot;:3,&quot;type&quot;:&quot;0&quot;,&quot;comment_num&quot;:0,&quot;props&quot;:null,&quot;post_index&quot;:2,&quot;pb_tpoint&quot;:null}}'
    # print(str2.replace('&quot;', '\"'))

    # ThreadInfo(tid).prepare()
    # a = ThreadInfo(tid)
    # a.prepare()
    # print(a)
    # get_thread_basic_info()

    # str = "http://m.tiebaimg.com/timg?wapp&quality=80&size=b150_150&subsize=20480&cut_x=0&cut_w=0&cut_y=0&cut_h=0&sec=1369815402&srctrace&di=b0040d56c398395101a15fb250730dd2&wh_rate=null&src=http%3A%2F%2Ftb1.bdstatic.com%2Ftb%2Fcms%2Ffrs%2Fbg%2Fdefault_avatar20141017.jpg"
    #
    # res = urlparse(str)
    # print(res.path.split('/')[-1])


    # get_thread_basic_info()
    # html_tree = inflate_detail_model()
    # info = ThreadInfo(tid)



    # root.head.title['src'] = 'KKK'
    # print(root.find_all(None, id = 'j_p_postlist'))
    # root.head.title.clear()
    # root.head.title.append('lalala')
    # print(root.head.title)
    # print(root.head)
    #
    # with open('model/test.html', 'w', encoding='utf8') as f:
    #     f.write(str(root))

    # print(HTML.tostring(root))

    # print(.tostring())

    # prepare_folder()


    # now = float(time.time()) * 1000
    # print(now)
    # print(int(now))
    #
    # print(datetime.utcfromtimestamp(time.time()))
    #
    # print(time.time())
    #
    # # 1471502365200
    # 1471503169169
    # # 1471502542530 786
