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

def parserVideo(driver, urlList, url_title_map, manifest_path):
	print("++++++++	parserVideo ++++++++++")
	url_m3u8_map = {}
	for i, href in enumerate(urlList):
		filename = href.split("/")[-1].split(".")[0]
		play_url = href.replace(filename, "play_"+filename)
		print("index:{0} url:{1}\t\t title:{2}".format(i,play_url,url_title_map[href]))
		driver.get(play_url)
		wait = WebDriverWait(driver, 600)
		wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
		# print("source_code:",driver.page_source)
		iframe = driver.find_element(By.TAG_NAME, "iframe")
		src = iframe.get_attribute("src")
		# print("video src:",src)
		m3u8_url = src.split("=")[1]
		web_url = m3u8_url[:8] + m3u8_url[8:].split("/",1)[0]
		print("main_m3u8:{0} web_url:{1}".format(m3u8_url, web_url))
		main_m3u8 = m3u8.load(m3u8_url)
		if len(main_m3u8.playlists) == 1:
			media = main_m3u8.playlists[0]
			# print("media:{0} stream_info:{1} absolute_uri:{2}".format(media,media.stream_info,media.absolute_uri))
			url_m3u8_map[href] = media.absolute_uri
			print("video m3u8:", media.absolute_uri)
		else:
			print("error: main m3u8 playlists length > 1, playlists:", main_m3u8.playlists)

	with open(manifest_path,"w+", encoding="utf-8") as file:
		for i, href in enumerate(urlList):
			filename = href.split("/")[-1].split(".")[0]
			m3u8_str = ""
			m3u8_url = url_m3u8_map.get(href, None)
			if m3u8_url != None:
				m3u8_str = "{0}\tout\\{1}.mp4\t2".format(m3u8_url, filename)
			file.write("{0}\t\t<{1}>\n{2}\n".format(href,url_title_map[href],m3u8_str))

def main(*args):
	print("args:",*args)
	# url = args[0]#"https://index.m3u8"
	# url = "https://baidu.com"
	web_url = "http://www.avtt421.com"
	tab_url = "/shipin4/avjieshuo/"
	driver_path = "E:/WorkSpaces/PythonSpaces/PythonTools/ParseHTML/geckodriver.exe"
	binary_location = "E:/LifeSofts/Mozilla Firefox/firefox.exe"
	pageBegin = 1	# 从第几页开始读取
	pageCount = 1	# 读取多少页的数据

	cacheFileName = tab_url.replace("/","_")

	profile = FirefoxProfile()
	profile.set_preference("permissions.default.image", 2)#禁止加载图片

	options = Options()
	options.binary_location = binary_location
	options.profile = profile

	service = Service(executable_path=driver_path)

	driver = webdriver.Firefox(options=options, service = service)
	# 尝试直接请求 返回的是认证页面
	driver.get(web_url+tab_url)
	
	# time.sleep(15)
	wait = WebDriverWait(driver, 600)
	wait.until(EC.presence_of_element_located((By.CLASS_NAME, "myButton")))

	print("current_url:",driver.current_url)
	print("title:",driver.title)
	# print("source_code:",driver.page_source)

	button = driver.find_element(By.CLASS_NAME, 'myButton')
	button.click()
	time.sleep(3)

	# 等待界面加载首页
	# wait = WebDriverWait(driver, 600)
	# wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu")))

	# print("current_url:",driver.current_url)
	# print("title:",driver.title)
	# print("source_code:",driver.page_source)

	# links = driver.find_elements(By.TAG_NAME, 'a')
	# target_link = None
	# for link in links:
	# 	print("link<{0}>: {1}".format(link.text,link.get_attribute('href')))
	# 	if( link.text == "AV解说"):
	# 		target_link = link
	
	# if target_link == None:
	# 	print("target_link not find")
	# 	driver.quit()
	# 	return

	# print("------------------------------")
	# print("target_link<{0}>: {1}".format(target_link.text,target_link.get_attribute('href')))
	# target_link.click()
	# target_link_href = target_link.get_attribute('href')

	
	url_list = []
	url_title_map = {}
	urlCacheFile = cacheFileName+"cache.txt"

	if os.path.exists(urlCacheFile):
		with open(urlCacheFile,"r", encoding="utf-8") as file:
			for line in file:
				infoList = line.split("\t\t")
				if len(infoList) == 2:
					url = infoList[0]
					title = infoList[1]
					url_list.append(url)
					url_title_map[url] = title[1:-1]
		parserVideo(driver, url_list, url_title_map, cacheFileName+"manifest.txt")
		return


	# 验证过后 重新请求
	# "http://www.avtt421.com" + "/shipin4/avjieshuo/" + "list_1.html"
	target_link_href = web_url+tab_url+"list_{0}.html".format(pageBegin)
	driver.get(target_link_href)

	wait = WebDriverWait(driver, 150)

	
	wait_window_time = 10
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
	
	for i in range(pageCount):
		if next_page_href != None:
			print("next_page:",next_page_href)
			driver.get(next_page_href)
			wait = WebDriverWait(driver, 150)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, "menu")))
		time.sleep(2)
		links = driver.find_elements(By.TAG_NAME, 'a')
		for link in links:
			href = link.get_attribute('href')
			if link.text == "下一页":
				next_page_href = href
			print("find link<{0}>: {1}".format(link.text,href))
			if len(href) > len(tab_url) and href.find(tab_url) >= 0:
				splitList = href.split("/")
				filename = splitList[-1].split(".")[0]
				if filename.isdigit():
					url_list.append(href)
					url_title_map[href] = link.text.replace("\n","")
		

	with open(urlCacheFile,"w+", encoding="utf-8") as file:
		for i, href in enumerate(url_list):
			file.write("{0}\t\t<{1}>\n".format(href,url_title_map[href]))
	
	parserVideo(driver, url_list, url_title_map, cacheFileName+"manifest.txt")
	print("sleep!!!")
	# driver.get(web_url+url)
	# # button = driver.find_element(By.CLASS_NAME, 'myButton')


	time.sleep(180)
	driver.quit()


def mainTest(*args):
	print("args:",*args)

if __name__ == "__main__":
	main(*sys.argv[1:])