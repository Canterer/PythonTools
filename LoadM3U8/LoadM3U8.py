import m3u8 
import os
import sys
import re
from Crypto.Cipher import AES
import glob
import concurrent.futures
import time
from concurrent.futures import as_completed
import requests
from urllib3 import disable_warnings
disable_warnings()
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
#http://vip8.3sybf.com/20230220/6PvSCFNx/700kb/hls/index.m3u8   output\9148713.mp4
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"
}
timeout = ()
bForceHttp = False

#防止ts名字过长
def fixLongFileName(filename):
    if len(filename) > 200:
        filename = filename[-30:]
    return filename

#正则表达判断是否为网站地址
def reurl(url):
    pattern = re.compile(r'^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+')
    if url is None:
        return False
    m=pattern.search(url)
    if m is None:
        return False
    else:
        return True

#超时重连
def send_request_get(url, max_retries, timeout):
    retries = 0
    print("get ",url)
    if bForceHttp and url[:5] == "https":
        print("change ts url protocol !!! https to http")
        #url = url[:4] + url[5:]
    while retries < max_retries:
        try:
            res = requests.get(url, stream=True, verify=False,headers=headers, timeout=timeout)
            if res.status_code == 200:
                return res
        except requests.exceptions.Timeout :
            print("requests.get url:{0} timeout , retries {1}".format(url,retries+1))
        except Exception as e:
            print("error requests.get url:{0} exception:{1}".format(url,e))
        retries += 1
    print("get url:{0} fail !!!".format(url))
    return None
#获取密钥
def getKey(keystr,prefix_url,web_ip_url):
    keyinfo= str(keystr)
    print("keyInfo:",keyinfo)
    method_pos= keyinfo.find('METHOD')
    comma_pos = keyinfo.find(",")
    print(comma_pos,len(keyinfo))
    if comma_pos == -1:
        return None,None
    method = keyinfo[method_pos:comma_pos].split('=')[1]
    if method == "NONE":
        return None,None
    uri_pos = keyinfo.find("URI")
    quotation_mark_pos = keyinfo.rfind('"')
    key_url = keyinfo[uri_pos:quotation_mark_pos].split('"')[1]
    if reurl(key_url) == False:
        if key_url[0] == "/":
            key_url = web_ip_url + key_url
        else:
            key_url = prefix_url + "/" + key_url
    print("key_url:",key_url)
    if bForceHttp and key_url[:5] == "https":
        print("change key url protocol !!! https to http")
        key_url = key_url[:4] + key_url[5:]
    res = requests.get(key_url,headers=headers)
    key = res.content
    print("getKey method:",method)
    try:
        print("getKey key:",key.decode('utf-8'))
    except Exception as e:
        print("getKey key:{0} exception:{1}".format(key,e))
    return method, key

#下载文件
#down_url:ts文件地址
#url:*.m3u8文件地址
#decrypt:是否加密
#down_path:下载地址
#key:密钥
def download(ts_info,prefix_url,web_ip_url,decrypt,down_path,key):
    ts_url = ts_info[0]
    filename = ts_info[1]
    down_url = ts_url
    if reurl(ts_url) == False:
        if ts_url[0] == "/":
            down_url = web_ip_url + ts_url
        else:
            down_url = prefix_url + "/" + ts_url
    res = send_request_get(down_url, 3, (30, 180))
    if res is None:
        return
    fixFileName = fixLongFileName(filename)
    ts_path = down_path+"/{0}".format(fixFileName)
    temp_ts_path = down_path+"/{0}.temp".format(fixFileName)
    if decrypt:
        cryptor =  AES.new(key, AES.MODE_CBC, key)
    with open(temp_ts_path,"wb+") as file:
        for chunk in res.iter_content(chunk_size=2048):
            if chunk:
                if decrypt:
                    file.write(cryptor.decrypt(chunk))
                else:
                    file.write(chunk)
    os.rename(temp_ts_path, ts_path)
    return down_url
    
#合并ts文件
#dest_file:合成文件名
#source_path:ts文件目录
#ts_list:文件列表
#delete:合成结束是否删除ts文件   
def merge_to_mp4(dest_file, source_path,ts_list, delete=False):
    files = glob.glob(source_path + '/*.ts')
    if len(files)!=len(ts_list):
        print("文件不完整！{0}!={1}".format(len(files),len(ts_list)))
        return
    dest_file = os.path.join("D:/FFmpeg/",dest_file)# 修改为临时存放地址
    folderPath = os.path.dirname(dest_file)
    print("folderPath:",folderPath)
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    with open(dest_file, 'wb') as fw:
        for ts_name in ts_list:
            file_name = fixLongFileName(ts_name)
            with open(source_path+"/"+file_name, 'rb') as fr:
                fw.write(fr.read())
            if delete:
                os.remove(source_path+"/"+file_name)
    print("merge_to_mp4 {0} finished".format(dest_file))

def main(*args):
    print("args:",*args)
    url = args[0]#"https://index.m3u8"
    delete_ts_flag = False
    out_file_name = None
    if len(args) > 1:
        delete_ts_flag = args[1]=="True"
    if len(args) > 2:
        out_file_name = args[2]
    
    print("bForceHttp:{0}".format(bForceHttp))
    print("url:{0} delete_ts_flag:{1}".format(url,delete_ts_flag))
    web_ip_url = url[:8]+url[8:].split("/",1)[0]
    prefix_url = url.rsplit("/",1)[0]
    print("web_ip_url :{0} \nprefix_url:{1}".format(web_ip_url,prefix_url))

    #设置下载路径
    down_root_path="tmp"
    sub_folder_index = 1
    if len(args) > 3:
        sub_folder_index = int(args[3])
    wordList = url[8:].split("/")
    if len(wordList) <= sub_folder_index:
        print("sub_folder_index need < ",len(wordList))
        return
    down_sub_folder=wordList[sub_folder_index]

    #判断是否需要创建文件夹
    if not os.path.exists(down_root_path):
        os.mkdir(down_root_path)
    down_path=os.path.join(down_root_path,down_sub_folder)
    print("down_path:",down_path)
    if not os.path.exists(down_path):
        os.mkdir(down_path)

    m3u8Path = down_path+"/_index.m3u8"
    if not os.path.exists(m3u8Path):
        print("get m3u8=",url)
        res = send_request_get(url, 3, (30, 180))
        if res is None:
            print("Request m3u8 error !!!")
            return
        with open(m3u8Path,"wb+") as file:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:                
                    file.write(chunk)

    #使用m3u8库获取文件信息                
    video = m3u8.load(m3u8Path)
    #video = m3u8.load(url)
    #设置是否加密标志
    decrypt = False
    key = None
    #判断是否加密
    print("video.keys:",video.keys)
    keysPath = down_path+"/_keys.txt"
    if not os.path.exists(keysPath):
        if len(video.keys) > 0 and video.keys[0] is not None:
            method,key =getKey(video.keys[0],prefix_url,web_ip_url)
            # 针对性特殊处理
            if len(video.keys) == 2 and video.keys[1] is not None:
                methodTemp,keyTemp = getKey(video.keys[1],prefix_url,web_ip_url)
                if methodTemp is not None:
                    method = methodTemp
                    key = keyTemp
            # 针对性特殊处理
            print("video method:{0} key:{1}".format(method,key))
            if method is not None:
                decrypt = True
                with open(keysPath,"wb+") as file:
                    file.write(key)
    else:
        decrypt = True
        with open(keysPath,"rb+") as file:
            key = file.read()
    
    
    #ts列表
    ts_name_list=[]
    unload_ts_info_list=[]
    #把ts文件名添加到列表中
    total_ts_num = len(video.segments)
    ts_name="ts_name_none"

    tempList = []
    prefixURLMap = {}
    prefixURL = ""
    prefixURLCount = 0
    filterPrefixURL = ""
    prefixURLMaxCount = 0
    for i,filename in enumerate(video.segments):
        if filename.uri is None:
            continue
        if reurl(filename.uri) or filename.uri[0] == "/":
            prefixURL = filename.uri.rsplit("/", 1)[0]
            prefixURLCount = prefixURLMap.get(prefixURL, 0)
            prefixURLMap[prefixURL] = prefixURLCount + 1
    for prefixURL,count in prefixURLMap.items():
        print("prefixURL={0} count={1}".format(prefixURL, count))
        if( prefixURLMaxCount < count ):
            prefixURLMaxCount = count
            filterPrefixURL = prefixURL
    for i,filename in enumerate(video.segments):
        if filename.uri is None:
            continue
        if( filterPrefixURL == "" or filename.uri.find(filterPrefixURL) != -1 ):
            tempList.append(filename)

    for i,filename in enumerate(tempList):
        if reurl(filename.uri) or filename.uri[0] == "/":
            ts_name = filename.uri.rsplit("/", 1)[1]
        else:
            ts_name = filename.uri
        if ts_name.find("?") != -1:
                ts_name = ts_name.split("?", 1)[0]
        ts_name_list.append(ts_name)
        if not os.path.exists(os.path.join(down_path,fixLongFileName(ts_name))):
            unload_ts_info_list.append([filename.uri,ts_name])
    #开启线程池
    with concurrent.futures.ThreadPoolExecutor() as executor:
        obj_list = []
        # begin = time.time()#记录线程开始时间
        unload_ts_num = len(unload_ts_info_list)
        print("unload_ts_num:",unload_ts_num)
        for i in range(unload_ts_num):
            obj = executor.submit(download,unload_ts_info_list[i],prefix_url,web_ip_url,decrypt,down_path,key)
            obj_list.append(obj)
        #查看线程池是否结束
        ts_count = 0
        for future in as_completed(obj_list):
            ts_count = ts_count + 1
            print("progress {0}%  Current/Total = {1}/{2} \n\t{3}".format(round(ts_count/unload_ts_num*100, 1),ts_count,unload_ts_num,future.result()))
    merge_to_mp4(out_file_name, down_path, ts_name_list, delete_ts_flag)#合并ts文件
    # # times = time.time() - begin #记录线程完成时间
    # # print(times)

def mainTest(*args):
    print("args:",*args)

if __name__ == "__main__":
    main(*sys.argv[1:])
