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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"
}

#正则表达判断是否为网站地址
def reurl(url):
    pattern = re.compile(r'^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+')
    m=pattern.search(url)
    if m is None:
        return False
    else:
        return True
 
#获取密钥
def getKey(keystr,url):
    keyinfo= str(keystr)
    method_pos= keyinfo.find('METHOD')
    comma_pos = keyinfo.find(",")
    method = keyinfo[method_pos:comma_pos].split('=')[1]
    uri_pos = keyinfo.find("URI")
    quotation_mark_pos = keyinfo.rfind('"')
    key_url = keyinfo[uri_pos:quotation_mark_pos].split('"')[1]
    if reurl(key_url) == False:
        key_url = url.rsplit("/", 1)[0] + "/" + key_url
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
def download(down_url,url,decrypt,down_path,key):
    if reurl(down_url) == False:
        filename = down_url
        down_url = url.rsplit("/", 1)[0] + "/" + down_url
    else:
        filename = down_url.rsplit("/", 1)[1]
    try:
        res = requests.get(down_url, stream=True, verify=False,headers=headers)
    except Exception as e:
        print("error requests.get url:{0} exception:{1}".format(down_url,e))
        return
    down_ts_path = down_path+"/{0}".format(filename)
    if decrypt:
        cryptor =  AES.new(key, AES.MODE_CBC, key)
    with open(down_ts_path,"wb+") as file:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                if decrypt:
                    file.write(cryptor.decrypt(chunk))
                else:
                    file.write(chunk)
    
#合并ts文件
#dest_file:合成文件名
#source_path:ts文件目录
#ts_list:文件列表
#delete:合成结束是否删除ts文件   
def merge_to_mp4(dest_file, source_path,ts_list, delete=False):
    files = glob.glob(source_path + '/*.ts')
    if len(files)!=len(ts_list):
        print("文件不完整！")
        return
    with open(dest_file, 'wb') as fw:
        for file in ts_list:
            with open(source_path+"/"+file, 'rb') as fr:
                fw.write(fr.read())
            if delete:
                os.remove(file)
    print("merge_to_mp4 {0} finished".format(dest_file))

def main(*args):
    print("args:",*args)
    url = args[0]#"https://index.m3u8"
    delete_ts_flag = False
    out_file_name = "result.mp4"
    if len(args) > 1:
        delete_ts_flag = bool(args[1])
    if len(args) > 1:
        out_file_name = args[2]
    
    print("url:{0} delete_ts_flag:{1}".format(url,delete_ts_flag))
    #使用m3u8库获取文件信息
    video = m3u8.load(url)
    #设置是否加密标志
    decrypt = False
    key = None
    #判断是否加密
    print("video.keys:",video.keys)
    if len(video.keys) > 0 and video.keys[0] is not None:
        method,key =getKey(video.keys[0],url)
        decrypt = True
    #设置下载路径
    down_root_path="tmp"
    down_sub_folder=url.rsplit("/", 2)[1]
    #判断是否需要创建文件夹
    if not os.path.exists(down_root_path):
        os.mkdir(down_root_path)
    down_path=os.path.join(down_root_path,down_sub_folder)
    print("down_path:",down_path)
    if not os.path.exists(down_path):
        os.mkdir(down_path)
    
    #ts列表
    ts_list=[]
    unload_ts_uri_list=[]
    #把ts文件名添加到列表中
    total_ts_num = len(video.segments)
    ts_name="ts_name_none"
    # for i in range(total_ts_num)
    for filename  in video.segments:
        if reurl(filename.uri):
            ts_name = filename.uri.rsplit("/", 1)[1]
        else:
            ts_name = filename.uri
        ts_list.append(ts_name)
        if not os.path.exists(os.path.join(down_path,ts_name)):
            unload_ts_uri_list.append(filename.uri)
    #开启线程池
    with concurrent.futures.ThreadPoolExecutor() as executor:
        obj_list = []
        # begin = time.time()#记录线程开始时间
        unload_ts_num = len(unload_ts_uri_list)
        print("unload_ts_num:",unload_ts_num)
        for i in range(unload_ts_num):
            obj = executor.submit(download,unload_ts_uri_list[i],url,decrypt,down_path,key)
            obj_list.append(obj)
		#查看线程池是否结束
        ts_count = 0
        for future in as_completed(obj_list):
            ts_count = ts_count + 1
            print("{0}/{1}=={2}".format(ts_count,unload_ts_num,ts_count/unload_ts_num*100))
            # print("{0}/{1}=={2}%%future.status:{3} {4}".format(ts_count,unload_ts_num,ts_count/unload_ts_num*100,future.status(),future))
    merge_to_mp4(out_file_name, down_path,ts_list,delete_ts_flag)#合并ts文件
    # times = time.time() - begin #记录线程完成时间
    # print(times)


if __name__ == "__main__":
    main(*sys.argv[1:])
