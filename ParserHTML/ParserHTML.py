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

Global_Web_Op_Wait_Time = 150
Global_Web_M3U8_Wait_Time = 300
Global_Driver_Num = 10
Global_Web_Black_list = [
	"ng.alubax.com",
	"kh.bahbou.com"#仅UC游览器
]

Global_Web_Dynamic_Url = ""
Global_Web_Tab_Str = "/shipin/"

class VideoInfo:
	def __init__(self, href, title):
		self.href = href
		self.title = title

		self.main_m3u8_url = ""
		self.m3u8_url = ""
		self.href = Global_Web_Dynamic_Url +"/" +self.href[8:].split("/",1)[1]
		# print("Dynamic_Url:",self.href)
		self.filename = href.split("/")[-1].split(".")[0]

	def UpdateMainUrl(self, main_m3u8_url):
		self.main_m3u8_url = main_m3u8_url

	def UpdateUrl(self, m3u8_url):
		self.m3u8_url = m3u8_url

	def GetPlayUrl(self):
		return self.href.replace(self.filename, "play_"+self.filename)

	def GetRecordStr(self):
		recordStr = ""
		if self.m3u8_url != "":
			recordStr = "{0}\tout\\{1}.mp4\t2".format(self.m3u8_url, self.filename)
		recordStr = "{0}\t\t<{1}>\n{2}\n".format(self.href,self.title, recordStr)
		return recordStr

	def GetTempRecordStr(self):
		return "{0}\t\t<{1}>\n{2}\n".format(self.href,self.title, self.main_m3u8_url)

def parserVideo(options, service, video_info_list, manifest_path):
	print("++++++++	parserVideo ++++++++++")	
	remove_url_map = {}
	content = ""
	content_line_count = 0 
	failed_video_info_list = []#记录文件中 搜索失败的视频信息
	manifest_path_temp = manifest_path.replace(".txt", "_cache.txt")
	# 通过记录文件 查找已搜索成功的视频信息
	if os.path.exists(manifest_path):
		with open(manifest_path, "r", encoding="utf-8") as file:
			firstLine = ""
			secondLine = ""
			count = 0
			for line in file:
				count = count + 1
				if count % 2 == 1:
					firstLine = line
				else:
					secondLine = line
					splitList = firstLine.split("\t\t")
					if len(splitList) == 2 and len(splitList[1]) > 2:
						href = splitList[0]
						title = splitList[1][1:-2]# <xxx>\n 最后一个字符为换行
						print("parse index:{0} href:{1} title:<{2}>".format(count/2, href, title))
						if firstLine[-3:] == ">>\n":
							firstLine = firstLine[:-2]+"\n"

						splitList = secondLine.split(".mp4")
						if len(splitList) == 2:
							remove_url_map[href] = True
							content = content+firstLine+secondLine
							content_line_count = content_line_count + 2
						else:
							failed_video_info_list.append(VideoInfo(href, title))
					else:
						print("parser video info error!!! in line:{0} content:{1}".format(count, firstLine))

		# 将搜索失败的视频 合并到当前列表中 一起查询
		with open(manifest_path, "w", encoding="utf-8") as file:
			file.write(content)
			print("file line count:{0}".format(content_line_count))


	main_m3u8_content = ""
	all_video_info_list = []#待请求m3u8的列表
	wait_video_info_list = []#待请求main_m3u8的列表
	remove_main_url_map = {}
	if os.path.exists(manifest_path_temp):
		# 中间备份过数据
		with open(manifest_path_temp, "r", encoding="utf-8") as file:
			firstLine = ""
			secondLine = ""
			count = 0
			for line in file:
				count = count + 1
				if count % 2 == 1:
					firstLine = line
				else:
					secondLine = line
					splitList = firstLine.split("\t\t")
					if len(splitList) == 2 and len(splitList[1]) > 2:
						href = splitList[0]
						title = splitList[1][1:-2]# <xxx>\n 最后一个字符为换行
						print("parse index:{0} href:{1} title:<{2}>".format(count/2, href, title))
						video_info = VideoInfo(href, title)
						video_info.UpdateMainUrl(secondLine[:-1])
						remove_main_url_map[href] = True
						all_video_info_list.append(video_info)
						main_m3u8_content = main_m3u8_content + firstLine + secondLine
					else:
						print("parser video info error!!! in line:{0} content:{1}".format(count, firstLine))


	for i, video_info in enumerate(video_info_list):
		if video_info.href not in remove_url_map:
			if video_info.href not in remove_main_url_map:
				wait_video_info_list.append(video_info)
	wait_video_info_list.extend(failed_video_info_list)# 追加之前失败的视频信息
	wait_video_info_num = len(wait_video_info_list)

	if wait_video_info_num > 0:
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
					with open(manifest_path_temp,"w", encoding="utf-8") as file:
						file.write(main_m3u8_content)
						for i, video_info in enumerate(wait_video_info_list):
							file.write(video_info.GetTempRecordStr())

				#查看线程池是否结束

		for i, driver in enumerate(driver_list):
			driver.quit()
		driver_list = []

		# 更新结果备份
		with open(manifest_path_temp,"w", encoding="utf-8") as file:
			file.write(main_m3u8_content)
			for i, video_info in enumerate(wait_video_info_list):
				file.write(video_info.GetTempRecordStr())
				all_video_info_list.append(video_info)


	update_video_info_list = concurrent_m3u8(all_video_info_list)
	with open(manifest_path,"w", encoding="utf-8") as file:
		file.write(content)
		for i, video_info in enumerate(update_video_info_list):
			file.write(video_info.GetRecordStr())

	# if os.path.exists(manifest_path_temp):
		# os.remove(manifest_path_temp)

def cache_func_test(data_list, isFinished):
	print("cache_func_test")
	# # 中间结果备份
	# with open(manifest_path_temp,"w", encoding="utf-8") as file:
	# 	file.write(main_m3u8_content)
	# 	for i, video_info in enumerate(wait_video_info_list):
	# 		file.write(video_info.GetTempRecordStr())

def task_pop_func_test(driver_index, result):
	print("task_pop_func_test")
	# driver_index, video_index, video_info = future.result()
	# print("driver_index {0} completed video_index:{1} main_m3u8_url:{2}".format(driver_index, video_index, video_info.main_m3u8_url))
def task_push_func_test(driver_index, data_index, data):
	print("task_push_func_test")
	# print("executor.submit driver_index {0} count:{1} href:{2}".format(driver_index, count, wait_video_info_list[count].href))
def task_run_func_test(driver, driver_index, data_index, data):
	print("task_run_func_test")

def concurrent_driver_func(driver_num,data_num,data_list,cache_step,cache_func,task_pop_func,task_push_func,task_run_func):
	# driver_num = Global_Driver_Num
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
					task_pop_func(driver_index, future.result)
					# driver_index, video_index, video_info = future.result()
					# print("driver_index {0} completed video_index:{1} main_m3u8_url:{2}".format(driver_index, video_index, video_info.main_m3u8_url))
					if count < data_num:
						task_push_func(driver_index, count, data_list[count])
						# print("executor.submit driver_index {0} count:{1} href:{2}".format(driver_index, count, wait_video_info_list[count].href))
						obj = executor.submit(task_run_func, driver_list[driver_index], driver_index, count, data_list[count])
						obj_cache_list.append(obj)
						count += 1
						wait_flag = True
			else:
				# 仅第一次会运行至此
				for index in range(driver_num):
					driver = driver_list[index]
					driver_auth(driver)
					if count < data_num:
						task_push_func(driver_index, count, data_list[count])						
						# print("executor.submit driver_index {0} count:{1} href:{2}".format(index, count, wait_video_info_list[count].href))
						obj = executor.submit(task_run_func, driver_list[index], index, count, data_list[count])
						obj_cache_list.append(obj)
						count += 1
						wait_flag = True
			
			if len(wait_video_info_list) >= cache_index:
				cache_index = cache_index + cache_size
				cache_func(wait_video_info_list, False)
				# # 中间结果备份
				# with open(manifest_path_temp,"w", encoding="utf-8") as file:
				# 	file.write(main_m3u8_content)
				# 	for i, video_info in enumerate(wait_video_info_list):
				# 		file.write(video_info.GetTempRecordStr())

			#查看线程池是否结束

	for i, driver in enumerate(driver_list):
		driver.quit()
	driver_list = []

	cache_func(wait_video_info_list, True)
	# # 更新结果备份
	# with open(manifest_path_temp,"w", encoding="utf-8") as file:
	# 	file.write(main_m3u8_content)
	# 	for i, video_info in enumerate(wait_video_info_list):
	# 		file.write(video_info.GetTempRecordStr())
	# 		all_video_info_list.append(video_info)



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
						file.write("{0}\t\t<{1}>\n".format(video_info.href, video_info.title))

			#查看线程池是否结束

	for i, driver in enumerate(driver_list):
		driver.quit()
	driver_list = []

	with open(urlCacheFile,"w", encoding="utf-8") as file:
		for i, video_info in enumerate(result_list):
			file.write("{0}\t\t<{1}>\n".format(video_info.href, video_info.title))




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
					video_info_list.append(VideoInfo(href, title))
	except Exception as e:
		print("req page {0} failed !!! url:{1}".format(page_index,page_url))
	return (driver_index, page_index, video_info_list)

def req_video_info(driver, driver_index, video_index, video_info):
	play_url = video_info.GetPlayUrl()
	print("driver_index:{0} video_index:{1} play_url:{2}".format(driver_index, video_index, play_url))
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

def main(*args):
	print("args:",*args)
	print("cwd:",os.getcwd())
	# url = args[0]#"https://index.m3u8"
	# url = "https://baidu.com"

	tab_url = Global_Web_Tab_Str
	pageBegin = 1	# 从第几页开始读取
	pageCount = 1	# 读取多少页的数据
	auto_max_page_flag = True # 是否自动扫描到最后一页

	# driver_path = "E:/WorkSpaces/PythonSpaces/PythonTools/ParserHTML/geckodriver.exe"
	driver_path = "./geckodriver.exe"
	driver_path = os.path.join(os.getcwd(), driver_path)
	binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
	print("driver_path:", driver_path)
	print("binary_location:", binary_location)
	print("tab_str:", tab_url)

	cacheFileName = tab_url.replace("/","_")

	profile = FirefoxProfile()
	profile.set_preference("permissions.default.image", 2)#禁止加载图片

	options = Options()
	options.binary_location = binary_location
	options.profile = profile
	options.add_argument('-headless')

	service = Service(executable_path=driver_path)

	driver = webdriver.Firefox(options=options, service = service)
	driver_auth(driver)

	
	# 等待界面加载首页
	# wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)
	# wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu")))

	# print("current_url:",driver.current_url)
	# print("title:",driver.title)
	# print("source_code:",driver.page_source)

	# links = driver.find_elements(By.TAG_NAME, 'a')
	# target_link = None
	# for link in links:
	# 	print("link<{0}>: {1}".format(link.text,link.get_attribute('href')))
	# 	if( link.text == "解说"):
	# 		target_link = link
	
	# if target_link == None:
	# 	print("target_link not find")
	# 	driver.quit()
	# 	return

	# print("------------------------------")
	# print("target_link<{0}>: {1}".format(target_link.text,target_link.get_attribute('href')))
	# target_link.click()
	# target_link_href = target_link.get_attribute('href')

	
	urlCacheFile = cacheFileName+"cache.txt"
	video_info_list = []

	if os.path.exists(urlCacheFile):
		with open(urlCacheFile,"r", encoding="utf-8") as file:
			for line in file:
				infoList = line.split("\t\t")
				if len(infoList) == 2:
					href = infoList[0]
					title = infoList[1]
					title = title[1:-2]# <xxx>\n 最后一个字符为换行
					video_info_list.append(VideoInfo(href, title))

		driver.quit()
		parserVideo(options, service, video_info_list, cacheFileName+"manifest.txt")
		return


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
	while count < pageCount:
	#for i in range(pageCount):
		count = count + 1
		if next_page_href != None:
			print("next_page:",next_page_href)
			driver.get(next_page_href)
			wait = WebDriverWait(driver, Global_Web_Op_Wait_Time)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu")))
		time.sleep(2)
		links = driver.find_elements(By.TAG_NAME, 'a')
		for link in links:
			href = link.get_attribute('href')
			if link.text == "下一页":
				next_page_href = href
			#print("find link<{0}>: {1}".format(link.text,href))
			if len(href) > len(tab_url) and href.find(tab_url) >= 0:
				# print("find link<{0}>: {1}".format(link.text,href))
				splitList = href.split("/")
				filename = splitList[-1].split(".")[0]
				if filename.isdigit():
					title = link.text.replace("\n","")
					video_info_list.append(VideoInfo(href, title))
				elif auto_max_page_flag and filename[:5] == "list_":
					if filename[5:].isdigit():
						page_index = int(filename[5:])
						if page_index > max_page:
							max_page = page_index
							print("update max_page:",max_page)
		if auto_max_page_flag and max_page != pageBegin + pageCount -1:
			pageCount = max_page - pageBegin + 1
			print("auto change pageCount:",pageCount)
			break
		if not auto_max_page_flag:
			break

	driver.quit()

	data_list = []
	for page_index in range(pageBegin,max_page+1,1):
		page_url = Global_Web_Dynamic_Url+tab_url+"list_{0}.html".format(page_index)
		print("page_url:",page_url)
		data_list.append(page_url)

	concurrent_page(data_list, urlCacheFile, tab_url)

	# with open(urlCacheFile,"w+", encoding="utf-8") as file:
	# 	for i, video_info in enumerate(video_info_list):
	# 		file.write("{0}\t\t<{1}>\n".format(video_info.href, video_info.title))
	
	# parserVideo(options, service, video_info_list, cacheFileName+"manifest.txt")
	print("sleep!!!")


	time.sleep(60)

def mainTest(*args):
	print("args:",*args)

if __name__ == "__main__":
	main(*sys.argv[1:])
