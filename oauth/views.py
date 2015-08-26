#coding=utf-8
from django.http import HttpResponseRedirect
from django.conf import settings
import urllib,  httplib
import time
import json

def login(request, template=''):
    next_url = request.GET.get('next_url')
    if next_url != None:
        request.session['login_next_url'] = next_url
    url = 'http://open.csdb.cn/oauth/authorize?client_id=' + settings.OAUTH_CLIENT_ID + '&redirect_uri=' + settings.OAUTH_REDIRECT_URI + '&response_type=code'
    return HttpResponseRedirect(url)

def logout(request, template=''):
    request.session.flush()
    url = request.GET.get('next_url')
    if url:
        return HttpResponseRedirect(url)
    return HttpResponseRedirect('/')

def callback(request, template = ''):
    '''
        回调函数
    '''
    error = request.GET.get('error', False)
    if error:
        pass
        return False
    else:
        code = request.GET.get('code')
        if code:
            print code
            token =  get_access_token(code)
            print token
            if token:
                request.session['access_token'] = token['access_token']
                request.session['refresh_token'] = token['refresh_token']
                request.session['expires_time'] = int(token['expires_in']) +  time.time()
                request.session['user_name'] = token['sdc_user_id']
                
    if request.session.has_key('login_next_url'):
        url = request.session['login_next_url']
        del request.session['login_next_url']
    else:
        url = '/'
    return HttpResponseRedirect(url)
        
    # return HttpResponseRedirect('/')

def get_access_token(code): 
    params = urllib.urlencode({
        'client_id': settings.OAUTH_CLIENT_ID ,
        'client_secret': settings.OAUTH_CLIENT_SECRET,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'grant_type' : 'authorization_code',
        'code' : code,
        })
    #定义一些文件头     
    headers = {"Content-Type":"application/x-www-form-urlencoded",     
               "Connection":"Keep-Alive","Referer":'http://nict.dcloud.cn/callback'}   
    #与网站构建一个连接     
    conn = httplib.HTTPSConnection("open.csdb.cn")  
    #开始进行数据提交   同时也可以使用get进行     
    conn.request(method="POST",url="/oauth/access_token",body=params,headers=headers)     
    #返回处理后的数据     
    
    response = conn.getresponse() 
    if response.status != 200:
        return False
    res = response.read()
    conn.close()
    return json.loads(res)

def refresh_access_token(request):
    params = urllib.urlencode({
        'client_id': settings.OAUTH_CLIENT_ID ,
        'client_secret': settings.OAUTH_CLIENT_SECRET,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'grant_type' : 'refresh_token',
        'refresh_token': request.session['refresh_token'],
        })
    #定义一些文件头     
    headers = {"Content-Type":"application/x-www-form-urlencoded",     
               "Connection":"Keep-Alive","Referer":'http://nict.dcloud.cn/callback'}   
    #与网站构建一个连接     
    conn = httplib.HTTPConnection("open.csdb.cn")  
    #开始进行数据提交   同时也可以使用get进行     
    conn.request(method="POST",url="/oauth/access_token", body=params, headers=headers)     
    #返回处理后的数据     
    response = conn.getresponse() 
    if response.status != 200:
        return False
    res = response.read()
    conn.close() 
    res = json.loads(res)
    if res['code']:
        return False
    request.session['access_token'] = res['access_token']
    request.session['refresh_token'] = res['refresh_token']
    request.session['expires_time'] = int(res['expires_in']) +  time.time()


def get_user_info(request):
    if request.session.has_key('user_info'):
        return request.session['user_info']
    url = '/res/getUserInfo/?username=' + request.session['user_name'] + '&access_token=' + request.session['access_token']
    #定义一些文件头     
    headers = {"Content-Type":"application/x-www-form-urlencoded",     
               "Connection":"Keep-Alive","Referer":'http://nict.dcloud.cn/callback'}   
    #与网站构建一个连接     
    conn = httplib.HTTPConnection("open.csdb.cn")  
    #开始进行数据提交   同时也可以使用get进行     
    conn.request(method="GET",url=url, body="", headers=headers)     
    #返回处理后的数据     
    response = conn.getresponse() 

    if response.status != 200:
        return False
    res = response.read()
    conn.close() 
    res = json.loads(res)
    if res.has_key('user'):
        request.session['user_info'] = res['user']
    return res['user']

