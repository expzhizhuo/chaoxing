
import requests as req
import base64
from time import sleep
from pyquery import PyQuery
import urllib.parse
from re import search
import json
import hashlib

requests = req.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
}

headers_without_type = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.37',
    "Referer": "https://mooc1.chaoxing.com/ananas/modules/video/index.html"
}


def print_json(s):
    print(json.dumps(s, indent=2, ensure_ascii=False))

def login(username, password):
    url = 'http://passport2.chaoxing.com/fanyalogin'

    password = base64.b64encode(password.encode()).decode()
    data = {
        'fid': 434,
        'uname': username,
        'password': password,
        'refer': 'http%3A%2F%2Fi.chaoxing.com',
        't': True,
        'forbidotherlogin': '0'
    }
    response = requests.post(url=url, headers=headers, data=data)
    res = response.json()
    print(response)
    return res


def lesson_list():
    requests.get(url='http://i.chaoxing.com', headers=headers_without_type)
    res = requests.post(url='http://mooc1-1.chaoxing.com/visit/interaction?showOldCourseView=1', headers= headers_without_type)
    # print(res.text)
    pq = PyQuery(res.text)
    # print(pq)
    lesson_info = pq('ul.clearfix li div')
    print('检测到你当前有{}门课程, 请选择你要进行学习的课程，输入对应的数字即可！'.format(lesson_info.__len__()))
    lesson_url_list = []
    # print(lesson_info)
    count = 0
    for lesson in lesson_info:
        pqq = PyQuery(lesson)
        print('==' * 50)
        count += 1
        print(count)
        href_pre = 'http://mooc1-1.chaoxing.com'
        href = pqq('h3 a').attr('href')
        if href:
            # print(href)
            lesson_url_list.append(href_pre + href)
            # get_list(href_pre + href)
            print(pqq('h3 a').attr('title'))
            print(pqq('p').text())
        else:
            print(pqq('h3').text())
            print('该课程暂未到开课时间')
            print(pqq('p').text())
        print('==' * 50)
    # print(lesson_url_list)
    while True:
        try:
            num = input('请输入对应课程的序号：')
            start_learn(lesson_url_list[int(num) - 1])
        except AttributeError as ee:
            print(ee)
            continue
        except ValueError as eee:
            print(eee.__str__())
            print(eee.__class__)
            continue
        except Exception as e:
            print(e.__str__())
            print(e.__class__)
            continue
        print('当前课程学习结束...')
        isc = input('是否继续学习,确认请输入y')
        if isc.lower() == 'y':
            continue
        return 1


def parse_url(url):
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
    return query


def start_learn(url):
    query = parse_url(url)
    courseid = query['courseid']
    clazzid = query['clazzid']
    cpi = query['cpi']
    vc = query['vc']  # 视频数量

    info_dict = {
        'courseid': courseid,
        'clazzid': clazzid,
        'cpi': cpi,
        'vc':vc,
    }

    res = requests.get(url=url, headers=headers_without_type)
    pq = PyQuery(res.text)
    links = pq('h3.clearfix a')
    for link in links:
        link_text = PyQuery(link).attr('href')
        utenc = get_utenc(link_text)
        info_dict['utenc'] = utenc
        chapterid = parse_url(link_text).get('chapterId')
        info_dict['chapterid'] = chapterid
        check_video_paper(**info_dict)
        sleep(0.3)


def get_utenc(url):
    url = 'http://mooc1-1.chaoxing.com' + url
    res = requests.get(url=url, headers=headers_without_type)
    utenc = search(r'utEnc="(.*)";', res.text).group(1)
    return utenc


# 检测学习任务 试题 视频
def check_video_paper(**kwargs):
    info_dict1 = kwargs
    data = 'courseId={courseid}&clazzid={clazzid}&chapterId={chapterid}&cpi={cpi}&verificationcode='.format(**info_dict1)
    url = 'https://mooc1-1.chaoxing.com/mycourse/studentstudyAjax'
    res = requests.post(url=url, data=data,headers=headers)
    # print(res.text)
    pq = PyQuery(res.text)
    if pq('h1').text() == '章节测验': # 这里为了匹配战略推演：商业竞争与制胜之道这门课
        print('总共有1个学习任务')
        info_dict1['num'] = 0
        learn_paper(**info_dict1)
        return
    elif len(pq('div.tabtags div')) == 2:
        print('总共有1个学习任务')
        info_dict1['num'] = 0
        learn_video(**info_dict1)
        return
    tasks = pq('div.tabtags span') # 所有的学习任务 包括视频和习题
    task_len = len(tasks)
    print('总共有{}个学习任务'.format(task_len))
    count = 0
    for task in tasks:
        type = PyQuery(task).attr('title')
        print(type, end=' ')
        if type == '章节测验' or type == '课后测验' or type == '章节测试':
            # 这里num即为count
            info_dict1['num'] = count
            learn_paper(**info_dict1)
            pass
        elif type == '视频':
            info_dict1['num'] = count
            learn_video(**info_dict1)
            pass
        elif type == '学习目标':
            info_dict1['num'] = count
            pass
        count += 1
    print()


def learn_video(**kwargs):
    info_dict3 = kwargs
    url = 'https://mooc1-1.chaoxing.com/knowledge/cards?clazzid={clazzid}&courseid={courseid}&knowledgeid={chapterid}&num={num}' \
          '&ut=s&cpi={cpi}&v=20160407-1'.format(**info_dict3)
    res = requests.get(url=url, headers=headers_without_type)
    res_s = search(r'mArg = {(.*);', res.text).group(0)[7:-1]
    res_j0 = json.loads(res_s)
    # if len(res_j0['attachments']) != 1:
    #     print()
    for info in res_j0['attachments']:
        tt = ''
        try:
            tt = info['type']
        except:
            break
        if tt != 'video':
             continue
        video_name = info['property']['name']
        print('当前视频：{}'.format(video_name))
        isPassed = False
        try:
            isPassed = info['isPassed']  # 是否看过 当看过一点存在该字段且为False，第一次看不存在
        except:
            print('第一次看该视频')
        sleep(3)#休眠3秒
        # 判断是否看过
        if isPassed:
            print('已经看过啦')
            continue

        objectId = info['objectId']
        jobid = info['jobid']
        otherInfo = info['otherInfo']

        info1 = res_j0['defaults']
        userid = info1['userid']
        clazzId = info1['clazzId']
        courseid = info1['courseid']
        cpi = info1['cpi']

        # 拿到dtoken
        print(objectId)
        res = requests.get(url='https://mooc1-1.chaoxing.com/ananas/status/{}?k=21427&flag=normal'.format(objectId),
                           headers=headers_without_type)
        print(res.json())
        res_j = res.json()
        dtoken = res_j['dtoken']
        duration = res_j['duration']
        print('++++++++')
        # print('dtoken:{}, duration:{}'.format(dtoken,duration))

        # 下面开始看视频啦
        enc = get_enc(clazzId, userid, jobid, objectId, duration, clipTime=duration)
        post_info = {
            'cpi': cpi,
            'dtoken': dtoken,
            'clazzId': clazzId,
            'duration': duration,
            'objectId': objectId,
            'otherInfo': otherInfo,
            'jobid': jobid,
            'userid': userid,
            'enc': enc,

        }
        url = 'https://mooc1-1.chaoxing.com/multimedia/log/a/{cpi}/{dtoken}?clazzId={clazzId}' \
              '&playingTime={duration}' \
              '&duration={duration}' \
              '&clipTime=0_{duration}' \
              '&objectId={objectId}' \
              '&otherInfo={otherInfo}&jobid={jobid}&userid={userid}&isdrag=4' \
              '&view=pc&enc={enc}&rt=0.9&dtype=Video&_t=1617424096544'.format(**post_info)
        res = requests.get(url=url, headers=headers_without_type)
        res_j1 = res.json()
        if res_j1['isPassed']:
            print('视频看完！')
            sleep(3)
        else:
            print('没看成功...')


def get_enc(clazzId, userid, jobid, objectId, duration, clipTime):
    loc4 = duration
    text = "[%s][%s][%s][%s][%s][d_yHJ!$pdA~5][%s][0_%s]" % (
        clazzId, userid, jobid, objectId, str(loc4 * 1000), str(duration * 1000), clipTime)
    hash = hashlib.md5()
    hash.update(text.encode(encoding='utf-8'))
    return hash.hexdigest()

def learn_paper(**kwargs):
    info_dict2 = kwargs
    url = 'https://mooc1-1.chaoxing.com/knowledge/cards?clazzid={clazzid}&courseid={courseid}&knowledgeid={chapterid}&num={num}' \
          '&ut=s&cpi={cpi}&v=20160407-1'.format(**info_dict2)
    res = requests.get(url=url, headers=headers_without_type)
    res_s = search(r'mArg = {(.*);', res.text).group(0)[7:-1]
    res_j0 = json.loads(res_s)
    get_paper_content(utenc=info_dict2['utenc'], **res_j0)
    '''
    {'jobid': 'work-4f774c90ca194a7a83d91e853976146c', 'otherInfo': 'nodeId_412182423-cpi_129173672', 
    'property': {'jobid': 'work-4f774c90ca194a7a83d91e853976146c', 'module': 'work', 
    'worktype': 'workA', 'mid': '1442049296661472432895315', 'title': '创新问题上中国与世界的关系', 
    'workid': '4f774c90ca194a7a83d91e853976146c', 
    '_jobid': 'work-4f774c90ca194a7a83d91e853976146c'},
     'mid': '1442049296661472432895315', 
     'enc': '357578a4bc7832f2653ea2a93d816d99', 
     'job': True, 'type': 'workid', 
     'aid': 737194922}
    '''
    '''
    workid jobid defaults->ktoken enc utenc 
    '''


# 获取试题信息
def get_paper_content(**kwargs):
    info_dict3 = kwargs
    url ='https://mooc1-1.chaoxing.com/api/work?api=1&workId={}' \
        '&jobid={}&needRedirect=true&knowledgeid={}' \
        '&ktoken={}&cpi={}&ut=s&clazzId={}&type=' \
        '&enc={}&utenc={}' \
        '&courseid={}'.format(
        info_dict3['attachments'][0]['property']['workid'],
        info_dict3['attachments'][0]['jobid'],
        info_dict3['defaults']['knowledgeid'],
        info_dict3['defaults']['ktoken'],
        info_dict3['defaults']['cpi'],
        info_dict3['defaults']['clazzId'],
        info_dict3['attachments'][0]['enc'],
        info_dict3['utenc'],
        info_dict3['defaults']['courseid'],
    )

    # 这里拿到了所有试题以及选项
    res = requests.get(url=url, headers=headers_without_type)
    # print(res.text)
    pq = PyQuery(res.text)
    # 判断是否已经做过了
    title = pq('title').text()
    if title == '查看已批阅作业':
        print('当前试题已经做过了')
        return

    post_url = pq('form#form1').attr('action')
    # 所有答案
    answers = pq('div.clearfix li')
    answer_str = ''
    for answer in answers:
        answer_str += PyQuery(answer).text().replace(' ', '').replace('\n', '').replace('，', ',')
        # 判断题的答案为true或false

    # 所有问题
    questions = pq('div.TiMu div.Zy_TItle div.clearfix')
    ans_list = []
    for question in questions:
        question_str = PyQuery(question).text()
        ans = query_answer(question_str.replace('\n', '')[5:])
        if ans == None:
            print('答案查询出错！！！')
            return

        if len(ans) == 2:
            # 判断题
            if ans[0] == '错误':
                answer = '错误'
                ans_list.append(answer)
                continue
            elif ans[0] == '正确':
                answer = '正确'
                ans_list.append(answer)
                continue
        ans_temp = ''
        for choice in ans:
            # 单选多选
            index = answer_str.find(choice)
            if index == -1:
                print('未找到答案')
                continue
            # answer_str = answer_str.replace(ans, '')
            answer = answer_str[index - 1] # ABCD
            if not answer.isupper():
                index = answer_str.rfind(choice)
                answer = answer_str[index - 1]
            try:
                answer = search(r'([A-Z])({})'.format(choice), answer_str).group(1)
            except:
                # answer = search(r'([A-Z])({})'.format(choice.replace('"', '').replace('(', '\(').replace(')', '\)')), answer_str.replace('“', '').replace('”', '')).group(1)
                try:
                    answer = search(r'([A-Z])({})'.format(choice.replace('"', '').replace('(', '\(').replace(')', '\)').replace('：', ':')), answer_str.replace('“', '').replace('”', '').replace('：', ':')).group(1)
                except:
                    print('当前试题答案匹配失败...')
                    print('请手动提交当前章节测试！')
                    return
            ans_temp += answer
        ans_temp = ''.join((lambda x: (x.sort(), x)[1])(list(ans_temp)))
        ans_list.append(ans_temp)



    answer_info = {

    }

    count = 0
    answerwqbid = ''
    inputs = pq('form#form1 input')
    check_list = []
    for inp in inputs:
        if 'checkbox' == PyQuery(inp).attr('type'):
            if len(check_list) == 0:
                check_list.append(PyQuery(inp).attr('name'))
            elif check_list[-1] != PyQuery(inp).attr('name'):
                check_list.append(PyQuery(inp).attr('name'))
        if 'hidden' != PyQuery(inp).attr('type'):
            continue
        field = PyQuery(inp).attr('name')
        # print(field, PyQuery(inp).attr('value'))
        answer_info[field] = PyQuery(inp).attr('value')

        if field.find('answertype') != -1:
            answer_info[field.replace('type', '')] = ans_list[count]
            count += 1
            answerwqbid += field.replace('answertype', '') + ','
    answer_info['answerwqbid'] = answerwqbid
    answer_info['pyFlag'] = ''

    count0 = 0
    ss = ''
    for i in ans_list:
        if i == 'true' or i == 'false' or len(i) == 1:
            continue
        for c in i:
            ss += '&{}={}'.format(check_list[count0], c)
        count0 += 1
    print_json(answer_info)
    # 根据试题进行查题 拿到答案
    print_json(kwargs)

    u = '&ua=pc&formType=post&saveStatus=1&pos=0fc50d4d2aa80b402902a5f5c4&rd=0.6444307876174606&value=(278|881)&wid=13174096&_edt=1617597580136245&version=1'
    print('正在提交答案...')
    sleep(0.4)
    url = 'https://mooc1-1.chaoxing.com/work/' + post_url
    data = urllib.parse.urlencode(answer_info)

    res = requests.post(url=url, headers=headers, data=data + ss)
    # print(res.request.body)
    res_j = res.json()
    print('当前提交状态：' + res_j['msg'])


def query_answer(question):
    url = 'https://q.zhizhuoshuma.cn/api.php'
    if question.find('（') > 5:
        question = question[:question.rfind('（')]
    # else:
    #     question = question.replace('（','').replace(' ）', '').replace('。', '')
    data = {
        'question':question
    }
    print('当前题目：{}'.format(question))
    print(question)
    res = requests.get(url=url, headers=headers, data=data).text
    print(res)
    if res.status_code == 200:
        answer = res
        print('查询到答案： {}'.format(answer))
        sleep(4)
        return answer.split('#')
    if res.status_code == -1:
        print('未检索到答案，请自行提交该题')


def main():
    print('支持自动刷视频以及自动刷题，对于部分题目查询不到答案，代码逻辑自动跳过了，需要你手动去做题....')
    print('''
                                  超星尔雅学习通自动答题
        ''')
    print('使用前请先使用浏览器打开 http://passport2.chaoxing.com/login?fid=&newversion=true&refer=http://i.chaoxing.com')
    print('确认自己的账号和密码能登录上再使用该软件进行刷课...')
    print('软件更新日期：2021年9月23日 20:15:45')
    print('问题反馈请联系作者：执着 微信：32590908')
    print('Free版禁止商业化使用！')
    while True:

        username = input('请输入账号：')
        password = input('请输入密码：')
        if username == '' or password == '':
            print('账号密码不能为空！请重新输入！')
            continue
        try:
            res = login(username=username, password=password)
            if not res['status']:
                print('登录失败...')
                print(res['msg2'])
                status = input('是否继续重新输入登录，是请输入y：')
                if status.lower() == 'y':
                    continue
                break
            print('登录成功...')
        except Exception as e:
            print(e.__class__)
            print(e.__str__())
            continue
        r = lesson_list()
        if r:
            break


if __name__ == '__main__':
    main()
