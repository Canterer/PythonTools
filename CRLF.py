#coding:utf-8
# 行尾一致修复

import os
import re
import sys
import stat

from functools import cmp_to_key

minEmptyRow = 0
suffixList = [".inl",".h",".cpp",".cs"]

def getFilesByFolder(folder, filePathList = []):
	folderPath = os.path.join(os.getcwd(),folder)
	# n = len(filePathList)
	for root,dirs,files in os.walk(folderPath):
		for file in files:
			filePathList.append(os.path.join(root,file))
	# m = len(filePathList)
	# print(folderPath, m-n)
	return filePathList

def checkSuffix(filePath):
	for suffix in suffixList:
		lenth = len(suffix)
		if filePath[-lenth:] == suffix:
			return True
	return False


def main(*args,**kwargs):
	print("行尾一致修复")
	filePathList = []
	if len(args) == 3 and args[1] == "-p":
		filePathList.append(os.path.join(os.getcwd(),args[2]))
	elif len(args) >= 2:
		for index,folder in enumerate(args):
			if index != 0:
				filePathList = getFilesByFolder(folder,filePathList)
	else:
		filePathList = getFilesByFolder("",filePathList)
	listLen = len(filePathList)
	i = 0
	j = 0
	pathList = []
	for filePath in filePathList:
		i = i + 1
		if checkSuffix(filePath):
			j = j + 1
			print(listLen,i,j)
			lastLine = ""
			lineCount = 0
			count = 0
			nextEmptyFlag = False
			FirstFlag = True
			with open(filePath,mode="r",encoding="utf-8",errors="ignore") as f:
				FindFlag = True
				for line in f:
					lineCount = lineCount + 1
					if nextEmptyFlag and line != "\n":
						FindFlag = False
						# print(filePath,"next error", lineCount)
						break
					if line != "\n":
						nextEmptyFlag = True
						if count != 0:
							if count%2 == 0 and not FirstFlag:
								FindFlag = False
								# print(filePath,"count error", count, lineCount)
								break
							count = 0
						FirstFlag = False
					else:
						nextEmptyFlag = False
						count = count + 1
					# print(lineCount, count, nextEmptyFlag, FirstFlag, line)
				if FindFlag:
					pathList.append([filePath,lineCount/2])
					# print(filePath)
	for filePathInfo in pathList:
		filePath = filePathInfo[0]
		if filePathInfo[1] > minEmptyRow:
			fileContent = ""
			Flag = False
			with open(filePath,mode="r",encoding="utf-8",errors="ignore") as f:
				for line in f:
					if line != "\n" or not Flag:
						fileContent = fileContent + line
						Flag = True
					else:
						Flag = False
			os.chmod(filePath,stat.S_IWUSR)
			with open(filePath,mode="w",encoding="utf-8",errors="ignore") as f:
				# print("###",fileContent)
				f.write(fileContent)
	def cmpFunc(a,b):
		if a[1] != b[1]:
			return a[1] < b[1]
		else:
			return a[0] < b[0]
	pathList.sort(key=cmp_to_key(cmpFunc))
	print("find path num:",len(pathList))
	for path in pathList:
		if path[1] > 6:
			print(path)

if __name__ == "__main__":
	main(*sys.argv)
