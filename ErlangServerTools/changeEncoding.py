#!usr/bin/python
import os
import sys
import re

G_Count = 0
G_MatchCount = 0
G_SpeCount = 0

def isHasChinese(string):
	for ch in string:
		if u'\u4e00' <= ch <= u'\u9fff':
			return True
	return False

def hasAddHead(content):
	# %%% -------------------------------------------------------------------
	# %%% 9秒社团全球首次开源发布
	# %%% http://www.9miao.com
	# %%% -------------------------------------------------------------------
	result = re.match("%{3} -+\n.*http://www.9miao.com\n.*%{3} -+\n", content, re.DOTALL)
	if result:
		return True
	else:
		return False

def deleteChineseLine(filePath,num):
	content = ""
	writeFlag = False
	global G_SpeCount,G_MatchCount
	with open(filePath, "r", encoding="utf-8", errors = "ignore") as f:
		count = 0
		for line in f:
			content+=line
			count+=1
			if count == num:
				break
		
		result = re.match("%{3} -+\n.*http://www.9miao.com\n.*%{3} -+\n", content, re.DOTALL)
		if result:
			spanTuple = result.span()
			content = content[:spanTuple[0]]+content[spanTuple[1]:]
			G_MatchCount+=1
			writeFlag = True
		else:
			G_SpeCount = G_SpeCount + 1
			print("{0} find line:{1}".format(filePath[-25:],content))
		# content = content.join(f.readlines())
		
		if not writeFlag:
			return
		else:
			for line in f:
				content+=line

	with open(filePath, "w", encoding="utf-8", errors = "ignore") as f:
		f.write(content)

def main(*args,**kargs):
	#sys.argv
	serverRoot = "G:\倾国倾城\倾国倾城全套源代码\倾国倾城服务器\wxserver"
	# serverRoot = os.getcwd()
	global G_Count,G_MatchCount
	for root, dirs, files in os.walk(serverRoot):
		for filePath in files:
			filePath = os.path.join(root,filePath)
			if filePath[-4:] == ".erl":
				fileTuple = os.path.split(filePath)
				G_Count = G_Count + 1
				# print(fileTuple[0][-15:],fileTuple[1])
				# gen_encode_info(os.path.join(root,filePath))
				deleteChineseLine(filePath,5)

	print("total filePath G_Count:",G_Count)
	print("G_MatchCount:",G_MatchCount)
	print("G_SpeCount:",G_SpeCount)

if __name__ == "__main__":
	main()