# import m3u8 
import os
import sys
import time
import m3u8

from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import concurrent.futures
from concurrent.futures import as_completed

import requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"
}

Global_Web_Op_Wait_Time = 1500
Global_Web_M3U8_Wait_Time = 300
Global_Driver_Num = 2
Global_Web_Black_list = [
	"ng.alubax.com",
	"kh.bahbou.com"#仅UC游览器
]

Global_Web_Dynamic_Url = "http://jrsa--06251124780.2565.48562.cwc001.yucc566.com"
# Global_Web_Tab_Str = "/shipin/"
Global_Web_Tab_Str = "/shipin4/guochanzhubo/"

class VideoInfo:
	def __init__(self, href, title):
		# self.href = href
		self.title = title

		self.main_m3u8_url = ""
		self.m3u8_url = ""
		self.img_url = ""
		self.cache_img_flag = False
		self.UpdateHref(href)
		# print("Dynamic_Url:",self.href)

	def UpdateHref(self, href):
		self.href = href
		if href != "":
			self.href = Global_Web_Dynamic_Url +"/" +self.href[8:].split("/",1)[1]
			self.filename = href.split("/")[-1].split(".")[0]

	def GetShortHref(self):
		if self.href != "":
			# print("Dynamic_Url:",self.href)
			return self.href[8:].split("/",1)[1]
		return ""

	def UpdateMainUrl(self, main_m3u8_url):
		self.main_m3u8_url = main_m3u8_url

	def UpdateUrl(self, m3u8_url):
		self.m3u8_url = m3u8_url

	def UpdateImgUrl(self, img_url):
		self.img_url = img_url

	def GetPlayUrl(self):
		return self.href.replace(self.filename, "play_"+self.filename)

	def GetCacheString(self):
		self.line = "{0}\t\t<{1}>\t\t{2}\t\t{3}\t\t{4}\t\t{5}\n".format(self.href,self.title,self.img_url,self.main_m3u8_url,self.m3u8_url,self.cache_img_flag)
		return self.line
	def ParseCacheString(self, line):
		self.line = line
		splitList = line.split("\t\t")
		if len(splitList) == 6:
			self.UpdateHref(splitList[0])
			self.title = splitList[1][1:-1]
			self.UpdateImgUrl(splitList[2])
			self.UpdateMainUrl(splitList[3])
			self.UpdateUrl(splitList[4])
			self.cache_img_flag = splitList[5][:-1]# \n 最后一个字符为换行

	def GetRecordStr(self):
		recordStr = ""
		if self.m3u8_url != "":
			recordStr = "{0}\tout\\{1}.mp4\t2".format(self.m3u8_url, self.filename)
		recordStr = "{0}\t\t<{1}>\t\t{2}\n{3}\n".format(self.href,self.title,self.img_url,recordStr)
		return recordStr

	def GetTempRecordStr(self):
		return "{0}\t\t<{1}>\t\t{2}\n{3}\n".format(self.href,self.title,self.img_url,self.main_m3u8_url)

def ParseFile(urlCacheFile):
	video_info_list = []
	with open(urlCacheFile,"r", encoding="utf-8") as file:
		for line in file:
			video_info = VideoInfo("","")
			video_info.ParseCacheString(line)
			video_info_list.append(video_info)
	print("ParseFile video_info_list num:",len(video_info_list))
	return video_info_list

def CacheFile(urlCacheFile, video_info_list, origin_video_info_list):
	if os.path.exists(urlCacheFile):
		if len(origin_video_info_list) == 0:
			with open(urlCacheFile,"r", encoding="utf-8") as file:
				for line in file:
					video_info = VideoInfo("","")
					video_info.ParseCacheString(line)
					origin_video_info_list.append(video_info)
	print("CacheFile() origin_video_info_list num:",len(origin_video_info_list))
	video_key_map = {}
	for i, video_info in enumerate(video_info_list):
		shortHref = video_info.GetShortHref()
		if shortHref != "":
			video_key_map[shortHref] = video_info
	print("CacheFile() video_info_list num:",len(video_info_list))
	content = ""
	if len(origin_video_info_list) < len(video_info_list):
		origin_video_info_list = video_info_list
	for i, video_info in enumerate(origin_video_info_list):
		shortHref = video_info.GetShortHref()
		if shortHref not in video_key_map:
			content += video_info.line
		else:
			origin_video_info_list[i] = video_key_map[shortHref]
			content += origin_video_info_list[i].GetCacheString()
	print("CacheFile() update origin_video_info_list num:",len(origin_video_info_list))
	with open(urlCacheFile,"w+", encoding="utf-8") as file:
		file.write(content)

def driver_auth(driver):
	web_url = "http://www.avtt421.com"
	# 第一次请求 返回的是线路选择
	driver.get(web_url)
	wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)
	time.sleep(3)
	# print("source_code",driver.page_source)
	#divs = driver.find_elements(By.TAG_NAME, "div")
	tag_a_list = driver.find_elements(By.TAG_NAME, "a")
	target_a = None
	for tag_a in tag_a_list:
		divs = tag_a.find_elements(By.TAG_NAME, "div")
		for div in divs:
			# print("div :",div.text)
			if div.text.find("线路一") == 0:
				target_a = tag_a
				href = tag_a.get_attribute('href')
				onclick = tag_a.get_attribute('onclick')
				# print("href:",href)
				# print("onclick:",onclick)

	next_auth_flag = False
	if target_a == None:
		next_auth_flag = True
		print("not find target line tag_a!!! this is auth page !!!")
	else:
		# print("find target line tag_a")
		target_a.click()
		time.sleep(3)

	if next_auth_flag:
		# 尝试直接请求 返回的是认证页面
		driver.get(web_url)
		# time.sleep(15)
		wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)
	# print("source_code:",driver.page_source)
	# wait.until(EC.presence_of_element_located((By.CLASS_NAME, "myButton")))

	# print("current_url:",driver.current_url)
	# print("title:",driver.title)
	# print("source_code:",driver.page_source)

	button = driver.find_element(By.CLASS_NAME, 'myButton')
	button.click()
	# print("click auth button")
	time.sleep(3)

	print("cur windows url:", driver.current_url)
	web_url = driver.current_url[:8] + driver.current_url[8:].split("/",1)[0]
	global Global_Web_Dynamic_Url
	Global_Web_Dynamic_Url = web_url
	print("dynamic web address:",web_url)
	print("driver auth finished!!!")

def concurrent_img(video_info_list, img_folder, cache_folder):
	if not os.path.exists(cache_folder):
		os.mkdir(cache_folder)
	if not os.path.exists(img_folder):
		os.mkdir(img_folder)
	#开启线程池
	with concurrent.futures.ThreadPoolExecutor() as executor:
		obj_list = []
		# begin = time.time()#记录线程开始时间
		unload_num = len(video_info_list)
		print("unload_num :",unload_num )
		for i, video_info in enumerate(video_info_list):
			obj = executor.submit(load_img, i, video_info, img_folder, cache_folder)
			obj_list.append(obj)
		#查看线程池是否结束
		count = 0
		for future in as_completed(obj_list):
			count = count + 1
			index, img_info = future.result()
			print("progress {0}%  Current/Total = {1}/{2} \n".format(round(count/unload_num*100, 1),count,unload_num))
	return video_info_list

def load_img(index, video_info, folder_path, cache_folder):
	splitList = video_info.img_url.split("/")
	img_full_name = splitList[-1]
	img_name = img_full_name.replace(".","_")
	if len(img_full_name.split(".")) < 2:
		print("error ",img_full_name)
		return index,video_info
	suffix = img_full_name.split(".")[1]
	cache_path = os.path.join(cache_folder,img_name)
	filename = video_info.title
	filename = filename.replace('*', '#')
	filename = filename.replace('<', '#')
	filename = filename.replace('>', '#')
	filename = filename.replace('?', '#')
	filename = filename.replace('\\', '#')
	filename = filename.replace('/', '#')
	filename = filename.replace('|', '#')
	filename = filename.replace(':', '#')
	filename = filename.replace('\"', '#')
	filename = video_info.filename + "=" + filename + "." + suffix
	dest_file = os.path.join(folder_path, filename)
	if os.path.exists(cache_path):
		if not os.path.exists(dest_file):
			with open(cache_path, 'rb') as fr:
				with open(dest_file, 'wb') as fw:
					fw.write(fr.read())
	else:
		# if not video_info.cache_img_flag:
		# 	return index, video_info
		res = send_request_get(video_info.img_url, 3, (30, 180))
		if res is None:
			return index, video_info
		with open(cache_path, 'wb') as fw:
			fw.write(res.content)
		with open(dest_file, 'wb') as fw:
			fw.write(res.content)
		video_info.cache_img_flag = True
	return index, video_info

def send_request_get(url, max_retries, timeout):
	retries = 0
	print("get ",url)
	bForceHttp = False
	if bForceHttp and url[:5] == "https":
		print("change ts url protocol !!! https to http")
		#url = url[:4] + url[5:]
	while retries < max_retries:
		try:
			res = requests.get(url, timeout=timeout)
			if res.status_code == 200:
				return res
		except requests.exceptions.Timeout :
			print("requests.get url:{0} timeout , retries {1}".format(url,retries+1))
		except Exception as e:
			print("error requests.get url:{0} exception:{1}".format(url,e))
		retries += 1
	print("get url:{0} fail !!!".format(url))
	return None

def concurrent_page(data_list, urlCacheFile, tab_url):
	data_num = len(data_list)
	driver_num = Global_Driver_Num
	driver_list = []
	driver_path = "./geckodriver.exe"
	driver_path = os.path.join(os.getcwd(), driver_path)
	binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
	for i in range(driver_num):
		print("try new driver index:",i)
		profile = FirefoxProfile()
		profile.set_preference("permissions.default.image", 2)#禁止加载图片
		options = Options()
		options.binary_location = binary_location
		options.profile = profile
		options.add_argument('-headless')
		service = Service(executable_path=driver_path)
		driver = webdriver.Firefox(options=options, service = service)
		# driver_auth(driver)
		driver_list.append(driver)
	print("open driver num:",driver_num)
	result_list = []
	#开启线程池
	with concurrent.futures.ThreadPoolExecutor() as executor:
		obj_list = []
		obj_cache_list = []
		# begin = time.time()#记录线程开始时间
		count = 0
		wait_flag = True
		cache_index = 300
		cache_size = cache_index
		while( wait_flag ):
			print("driver progress:{0}/{1}".format(count, data_num))
			obj_list = obj_cache_list
			obj_cache_list = []
			if len(obj_list) > 0:
				wait_flag = False
				for future in as_completed(obj_list):#每drive
					# task_pop_func(driver_index, future.result)
					driver_index, page_index, video_info_list = future.result()
					result_list.extend(video_info_list)
					print("driver_index {0} completed page_index:{1} video_list len:{2}".format(driver_index, page_index, len(video_info_list)))
					if count < data_num:
						# task_push_func(driver_index, count, data_list[count])
						print("executor.submit driver_index {0} count:{1} data:{2}".format(driver_index, count, data_list[count]))
						obj = executor.submit(req_page_info, driver_list[driver_index], driver_index, count, data_list[count], tab_url)
						obj_cache_list.append(obj)
						count += 1
						wait_flag = True
			else:
				# 仅第一次会运行至此
				for driver_index in range(driver_num):
					driver = driver_list[driver_index]
					driver_auth(driver)
					if count < data_num:
						# task_push_func(driver_index, count, data_list[count])						
						print("executor.submit driver_index {0} count:{1} data:{2}".format(driver_index, count, data_list[count]))
						obj = executor.submit(req_page_info, driver_list[driver_index], driver_index, count, data_list[count], tab_url)
						obj_cache_list.append(obj)
						count += 1
						wait_flag = True
			
			if count >= cache_index:
				cache_index = cache_index + cache_size
				print("update cache count:",count)
				# cache_func(wait_video_info_list, False)
				# # 中间结果备份
				with open(urlCacheFile,"w", encoding="utf-8") as file:
					for i, video_info in enumerate(result_list):
						file.write(video_info.GetCacheString())

			#查看线程池是否结束

	for i, driver in enumerate(driver_list):
		driver.quit()
	driver_list = []

	with open(urlCacheFile,"w", encoding="utf-8") as file:
		for i, video_info in enumerate(result_list):
			file.write(video_info.GetCacheString())

def req_page_info(driver, driver_index, page_index, page_url, tab_url):
	print("driver_index:{0} page_index:{1} page_url:{2}".format(driver_index, page_index, page_url))
	video_info_list = []
	try:
		driver.get(page_url)
		wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)
		wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu")))
		time.sleep(2)
		links = driver.find_elements(By.TAG_NAME, 'a')
		for link in links:
			href = link.get_attribute('href')
			#print("find link<{0}>: {1}".format(link.text,href))
			if len(href) > len(tab_url) and href.find(tab_url) >= 0:
				# print("find link<{0}>: {1}".format(link.text,href))
				splitList = href.split("/")
				filename = splitList[-1].split(".")[0]
				if filename.isdigit():
					title = link.text.replace("\n","")
					img_url = ""
					try:
						img = link.find_element(By.TAG_NAME,'img')
						img_url = img.get_attribute('src')
						# print("img_url ",img_url)
					except Exception as e:
						print("not find img_url by link:",href)
					video_info = VideoInfo(href, title)
					video_info.UpdateImgUrl(img_url)
					video_info_list.append(video_info)
	except Exception as e:
		print("req page {0} failed !!! url:{1}".format(page_index,page_url))
	return (driver_index, page_index, video_info_list)

def parserVideo(driver_path, binary_location,video_info_list,origin_video_info_list, manifest_path):
	print("++++++++	parserVideo ++++++++++")
	content = ""
	content_line_count = 0 
	wait_video_info_list = video_info_list
	wait_video_info_num = len(wait_video_info_list)
	manifest_path_temp = manifest_path.replace(".txt", "_cache.txt")
	if wait_video_info_num > 0:
		driver_num = Global_Driver_Num
		driver_list = []
		
		for i in range(driver_num):
			print("try new driver index:",i)
			profile = FirefoxProfile()
			profile.set_preference("permissions.default.image", 2)#禁止加载图片

			options = Options()
			options.binary_location = binary_location
			options.profile = profile
			options.add_argument('-headless')
			service = Service(executable_path=driver_path)
			driver = webdriver.Firefox(options=options, service = service)
			# driver_auth(driver)
			driver_list.append(driver)
		print("open driver num:",driver_num)
		#开启线程池
		with concurrent.futures.ThreadPoolExecutor() as executor:
			obj_list = []
			obj_cache_list = []
			# begin = time.time()#记录线程开始时间
			count = 0
			wait_flag = True
			cache_index = 10
			cache_size = cache_index
			while( wait_flag ):
				print("driver progress:{0}/{1}".format(count,wait_video_info_num))
				obj_list = obj_cache_list
				obj_cache_list = []
				if len(obj_list) > 0:
					wait_flag = False
					for future in as_completed(obj_list):#每drive
						driver_index, video_index, video_info = future.result()
						print("driver_index {0} completed video_index:{1} main_m3u8_url:{2}".format(driver_index, video_index, video_info.main_m3u8_url))
						if count < wait_video_info_num:
							print("executor.submit driver_index {0} count:{1} href:{2}".format(driver_index, count, wait_video_info_list[count].href))
							obj = executor.submit(req_video_info, driver_list[driver_index], driver_index, count, wait_video_info_list[count])
							obj_cache_list.append(obj)
							count += 1
							wait_flag = True
				else:
					# 仅第一次会运行至此
					for index in range(driver_num):
						driver = driver_list[index]
						driver_auth(driver)
						if count < wait_video_info_num:
							print("executor.submit driver_index {0} count:{1} href:{2}".format(index, count, wait_video_info_list[count].href))
							obj = executor.submit(req_video_info, driver_list[index], index, count, wait_video_info_list[count])
							obj_cache_list.append(obj)
							count += 1
							wait_flag = True
				
				if len(wait_video_info_list) >= cache_index:
					cache_index = cache_index + cache_size
					# 中间结果备份
					CacheFile(manifest_path_temp, wait_video_info_list, origin_video_info_list)

				#查看线程池是否结束

		for i, driver in enumerate(driver_list):
			driver.quit()
		driver_list = []

		# 更新结果备份
		CacheFile(manifest_path_temp, wait_video_info_list, origin_video_info_list)


def req_video_info(driver, driver_index, video_index, video_info):
	play_url = video_info.GetPlayUrl()
	print("driver_index:{0} video_index:{1} play_url:{2}".format(driver_index, video_index, play_url))
	if video_info.main_m3u8_url != "":
		return (driver_index, video_index, video_info)
	m3u8_url = ""
	try:
		driver.get(play_url)
		wait = WebDriverWait(driver, Global_Web_M3U8_Wait_Time)
		wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
		# print("source_code:",driver.page_source)
		iframe = driver.find_element(By.TAG_NAME, "iframe")
		src = iframe.get_attribute("src")
		# print("video src:",src)
		m3u8_url = src.split("=")[1]
		web_url = m3u8_url[:8] + m3u8_url[8:].split("/",1)[0]
		# print("main_m3u8:{0} web_url:{1}".format(m3u8_url, web_url))
	except Exception as e:
		print("load m3u8 failed !!! url:",play_url)
	video_info.UpdateMainUrl(m3u8_url)
	return (driver_index, video_index, video_info)

def concurrent_m3u8(video_info_list):
	#开启线程池
	with concurrent.futures.ThreadPoolExecutor() as executor:
		obj_list = []
		# begin = time.time()#记录线程开始时间
		unload_num = len(video_info_list)
		print("unload_num :",unload_num )
		for i, video_info in enumerate(video_info_list):
			obj = executor.submit(get_video_m3u8, i, video_info, 3)
			obj_list.append(obj)
		#查看线程池是否结束
		count = 0
		for future in as_completed(obj_list):
			count = count + 1
			index, video_info = future.result()
			video_info_list[index] = video_info
			print("progress {0}%  Current/Total = {1}/{2} \n".format(round(count/unload_num*100, 1),count,unload_num))
	return video_info_list

def get_video_m3u8(index, video_info, max_retries):
	if video_info.main_m3u8_url == "":
		print("get_video_m3u8 failed !!! main_m3u8_url is empty string ! href:", video_info.href)
		return (index, video_info)
	if video_info.m3u8_url != "":
		return (index, video_info)
	for limit in Global_Web_Black_list:
		if video_info.main_m3u8_url.find(limit) > 0:
			print("get_video_m3u8 failed !!! limit web:{0} main_m3u8_url:{1} href:{2}".format(limit, video_info.main_m3u8_url, video_info.href))
			return (index, video_info)
	retries = 0
	while retries < max_retries:
		retries += 1
		try:
			main_m3u8 = m3u8.load(video_info.main_m3u8_url)
			if len(main_m3u8.playlists) == 1:
				media = main_m3u8.playlists[0]
				# print("media:{0} stream_info:{1} absolute_uri:{2}".format(media,media.stream_info,media.absolute_uri))
				print("find video m3u8:", media.absolute_uri)
				video_info.UpdateUrl(media.absolute_uri)
				break
			else:
				print("error: main m3u8 playlists length > 1, playlists:{0} \nmain m3u8:{1}".format(main_m3u8.playlists, video_info.main_m3u8_url))
				break
		except Exception as e:
			print("load m3u8 failed !!! retries {0} url:{1}".format(retries, video_info.main_m3u8_url))
	return (index, video_info)

def main(*args):
	print("args:",*args)
	print("cwd:",os.getcwd())
	# url = args[0]#"https://index.m3u8"
	# url = "https://baidu.com"

	tab_url = Global_Web_Tab_Str
	cache_stage_page = 25 #每25页缓存一次数据
	

	# driver_path = "E:/WorkSpaces/PythonSpaces/PythonTools/ParserHTML/geckodriver.exe"
	driver_path = "./geckodriver.exe"
	driver_path = os.path.join(os.getcwd(), driver_path)
	binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
	print("driver_path:", driver_path)
	print("binary_location:", binary_location)
	print("tab_str:", tab_url)

	cacheFileName = tab_url.replace("/","_")
	video_info_list = []
	origin_video_info_list = []

	state_list = []
	# state_list.append(0)#统计每页数据至video_info_list
	# state_list.append(1)#从video_info_list缓存所有数据至 total_cache.txt
	# state_list.append(2)#合并所有缓存数据 至  total_cache.txt
	# state_list.append(3)#从total_cache.txt读取数据组成video_info_list 并下载img
	# state_list.append(4)# 指定页加载 多线程 读取每一页的数据并存储成 total_cache.txt
	# state_list.append(5)#从total_cache.txt读取数据组成video_info_list 并多线程读取main_m3u8_url
	# state_list.append(6)#从video_info_list多线程读取m3u8_url
	state_list.append(7)#可选输入参数 scan_folder outFileName
	for i, state in enumerate(state_list):
		if state == 0 :#统计每页数据至video_info_list
			pageBegin = 1	# 从第几页开始读取
			pageCount = 2	# 读取多少页的数据
			# auto_max_page_flag = True # 是否自动扫描到最后一页
			auto_max_page_flag = False # 是否自动扫描到最后一页

			profile = FirefoxProfile()
			profile.set_preference("permissions.default.image", 2)#禁止加载图片
			options = Options()
			options.binary_location = binary_location
			options.profile = profile
			options.add_argument('-headless')
			service = Service(executable_path=driver_path)

			driver = webdriver.Firefox(options=options, service = service)
			driver_auth(driver)

			# 验证过后 重新请求
			target_link_href = Global_Web_Dynamic_Url+tab_url+"list_{0}.html".format(pageBegin)
			driver.get(target_link_href)

			wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)

			wait_window_time = 20
			time.sleep(wait_window_time)
			target_window_handle = None
			for handle in driver.window_handles:
				driver.switch_to.window(handle)
				print("window_handle url:",driver.current_url)
				print("target_link_href url:",target_link_href)
				print("result:",driver.current_url.find(target_link_href))
				if target_link_href == driver.current_url or driver.current_url.find(target_link_href) >= 0:
					target_window_handle = handle

			if target_window_handle == None:
				print("target_window_handle not find in timeout {0}".format(wait_window_time))
				driver.quit()
				return

			driver.switch_to.window(target_window_handle)
			print("current_url:",driver.current_url)
			print("title:",driver.title)
			# print("source_code:",driver.page_source)

			next_page_href = None
			max_page = pageBegin + pageCount - 1
			count = 0
			cache_count = 0
			lastCacheIndex = 0
			while count < pageCount:
			#for i in range(pageCount):
				count = count + 1
				print("count:",count," pageCount:",pageCount)
				if next_page_href != None:
					print("next_page:",next_page_href)
					driver.get(next_page_href)
					wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)
					wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu")))
				time.sleep(2)
				links = driver.find_elements(By.TAG_NAME, 'a')
				for link in links:
					# print("outerHTML ",link.get_attribute('outerHTML'))
					href = link.get_attribute('href')
					if link.text == "下一页":
						next_page_href = href
						print("find next_page_href: {0}".format(next_page_href))
					#print("find link<{0}>: {1}".format(link.text,href))
					if len(href) > len(tab_url) and href.find(tab_url) >= 0:
						# print("find link<{0}>: {1}".format(link.text,href))
						splitList = href.split("/")
						filename = splitList[-1].split(".")[0]
						if filename.isdigit():
							title = link.text.replace("\n","")
							img_url = ""
							try:
								img = link.find_element(By.TAG_NAME,'img')
								img_url = img.get_attribute('src')
								# print("img_url ",img_url)
							except Exception as e:
								print("not find img_url by link:",href)
							video_info = VideoInfo(href, title)
							video_info.UpdateImgUrl(img_url)
							video_info_list.append(video_info)
						elif auto_max_page_flag and filename[:5] == "list_":
							if filename[5:].isdigit():
								page_index = int(filename[5:])
								if page_index > max_page:
									max_page = page_index
									print("update max_page:",max_page)
				if auto_max_page_flag and max_page != pageBegin + pageCount -1:
					pageCount = max_page - pageBegin + 1
					print("auto change pageCount:",pageCount)

				bLastCache = count == pageCount 
				if cache_count + cache_stage_page == count or bLastCache:
					urlCacheFile = cacheFileName+"total_cache_{0}_{1}.txt".format(pageBegin+cache_count,pageBegin+cache_count+cache_stage_page-1)
					cache_count = cache_count + cache_stage_page
					with open(urlCacheFile,"w+", encoding="utf-8") as file:
						for i, video_info in enumerate(video_info_list):
							if i > lastCacheIndex:
								file.write(video_info.GetCacheString())
						lastCacheIndex = len(video_info_list)-1

			driver.quit()

		if state == 1 :#从video_info_list缓存所有数据至 total_cache.txt
			# urlCacheFile = cacheFileName+"total_cache_1_25.txt"
			# video_info_list = ParseFile(urlCacheFile)
			urlCacheFile = cacheFileName+"total_cache.txt"
			CacheFile(urlCacheFile,video_info_list,origin_video_info_list)

		if state == 2 :#合并所有缓存数据 至  total_cache.txt
			urlCacheFile = cacheFileName+"total_cache.txt"
			index = 1
			content = ""
			flag = True
			tempMap = {}
			while True:
				cur_path = "{0}total_cache_{1}_{2}.txt".format(cacheFileName, index, index+cache_stage_page-1)
				print("try get path:",cur_path)
				if os.path.exists(cur_path):
					index = index + cache_stage_page
					with open(cur_path,"r", encoding="utf-8") as file:
						content = content + file.read()
				else:
					break
			if index > 1:
				with open(urlCacheFile,"w+", encoding="utf-8") as file:
					file.write(content)
					file.flush()

		if state == 3 :#从total_cache.txt读取数据组成video_info_list 并下载img
			urlCacheFile = cacheFileName+"total_cache.txt"
			video_info_list = ParseFile(urlCacheFile)
			
			concurrent_img(video_info_list, cacheFileName, "cache")

			print("sleep!!!")
			time.sleep(60)
			return

		if state == 4 :#多线程 读取每一页的数据并存储成 total_cache.txt
			data_list = []
			pageBegin = 1
			max_page = 3
			urlCacheFile = cacheFileName+"total_cache1.txt"
			for page_index in range(pageBegin,max_page+1,1):
				page_url = Global_Web_Dynamic_Url+tab_url+"list_{0}.html".format(page_index)
				print("page_url:",page_url)
				data_list.append(page_url)

			concurrent_page(data_list, urlCacheFile, tab_url)

		if state == 5:#从total_cache.txt读取数据组成video_info_list 并多线程读取main_m3u8_url
			urlCacheFile = cacheFileName+"total_cache1.txt"
			video_info_list = ParseFile(urlCacheFile)
			parserVideo(driver_path, binary_location, video_info_list, origin_video_info_list, urlCacheFile)

		if state == 6:#从video_info_list多线程读取m3u8_url
			urlCacheFile = cacheFileName+"total_cache1.txt"
			concurrent_m3u8(video_info_list)
			CacheFile(urlCacheFile, video_info_list, origin_video_info_list)
			manifest_path = cacheFileName+"manifest.txt"
			with open(manifest_path,"w", encoding="utf-8") as file:
				for i, video_info in enumerate(origin_video_info_list):
					file.write(video_info.GetRecordStr())

		if state == 7:#可选输入参数 scan_folder outFileName
			if len(args) < 1:
				print("need first arg as folder!!!")
				return
			folder = args[0]#"https://index.m3u8"
			scan_path = os.path.join(os.getcwd(), folder)
			print("scan_path:",scan_path)

			cacheFileName = tab_url.replace("/","_")
			manifest_path = cacheFileName+"total_cache.txt"
			outFileName = folder+"_input.txt"
			if len(args) >= 2:
				outFileName = args[1] + ".txt"

			print("outFileName:", outFileName)

			filenameMap = {}
			index = 0
			indexMap = {}
			recordMap = {}
			for root, dirs, files in os.walk(scan_path):
				for file in files:
					key = file.split("=")[0]
					filenameMap[key] = file
					indexMap[index] = key
					index = index + 1

			content = ""
			video_info_list = ParseFile(manifest_path)
			if len(video_info_list) == 0:
				print("can't find manifest file: ",manifest_path)
			for i, video_info in enumerate(video_info_list):
				if video_info.filename in filenameMap:
					filenameMap[video_info.filename] = False
					recordMap[video_info.filename] = video_info.GetRecordStr()
			for index, key in indexMap.items():
				if key in recordMap:
					content = content + recordMap[key]

			with open(outFileName,"w+", encoding="utf-8") as file:
				file.write(content)

			for key, value in filenameMap.items():
				if value:
					print("can't find file info : ", value)

def mainTest(*args):
	print("args:",*args)

if __name__ == "__main__":
	main(*sys.argv[1:])
