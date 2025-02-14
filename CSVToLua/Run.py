#coding:utf-8
import os
import re
import sys
import json
import csv
import time
import copy

DefaultProjectPath = None #工程根目录
DefaultTargetLuaFolder = os.path.join("..","ClientLuaData")#生成的lua文件夹路径
DefaultCSVFolder = os.path.join("..","..","..","Documents","csv")#读取的CSV文件夹路径 
DefaultRuleFolder = ""#定义的规则所在文件夹路径

def GetTagNameString(content):
	result = re.search("\(TagName=\"(.*?)\"\)",content)
	if result:
		return result.group(1)

def GetTagsList(content):
	tagNameList = []
	result = re.match("\(GameplayTags=\((.*)\)\)", content)
	if result:
		listContent = result.group(1)
		tagContentList = re.split(",",listContent)
		for tagContent in tagContentList:
			tagName = GetTagNameString(tagContent)
			if tagName and tagName != "":
				tagNameList.append(tagName)
	return tagNameList

def GetAssetIconPath(content):
	result = re.match("(.*)\/Icon\/(.*?)\/Frames\/(.*)_(.*?)_png\.(.*)_(.*?)_png", content)
	if result:
		folder = result.group(2)
		iconName = result.group(3)
		iconTag = result.group(4)
		iconNameT = result.group(5)
		iconTagT = result.group(6)
		if iconName != iconNameT :
			printError("GetAssetIconPath: config data is Error {0}_{1}_png.{2}_{3}_png".format(iconName,iconTag,iconNameT,iconTagT))
		if iconTag != iconTagT :
			printError("GetAssetIconPath: config data is Error {0}_{1}_png.{2}_{3}_png".format(iconName,iconTag,iconNameT,iconTagT))
		return tuple([folder,iconName,iconTag])
	else:
		return tuple()

def GetBracketRange(content,leftChar,rightChar):
	leftIndex = content.find(leftChar)
	rightIndex = len(content)-1
	if leftIndex == -1:
		print("wrong bracket style! can't find leftChar")
		return (0,0)
	index = leftIndex + 1
	endIndex = len(content)
	leftCharCount = 1
	rightCharCount = 0
	while index < endIndex and leftCharCount != rightCharCount:
		char = content[index]
		if char == leftChar:
			leftCharCount = leftCharCount + 1
		elif char == rightChar:
			rightCharCount = rightCharCount + 1
		index+=1
		if leftCharCount < rightCharCount:
			print("wrong bracket style! leftCharCount={0} < rightCharCount={1}".format(leftCharCount,rightCharCount))
			return (0,0)
		else:
			rightIndex = index#更新结束位置

	if leftCharCount == rightCharCount:
		return (leftIndex,rightIndex)
	else:
		print("wrong bracket style! find all leftCharCount={0} > rightCharCount={1}".format(leftCharCount,rightCharCount))
		return (0,0)

RuleFilePrintDic = {}
RuleFilePrintName = None
RuleFilePrintState = 0# 0代表无打印
def setPrintFile(fileName):
	global RuleFilePrintName,RuleFilePrintDic
	RuleFilePrintName = fileName
	RuleFilePrintDic.setdefault(fileName, [])

def printError(errorStr):
	global RuleFilePrintName,RuleFilePrintDic
	if RuleFilePrintName:
		printList = RuleFilePrintDic.get(RuleFilePrintName)
		if printList is not None:
			printList.append(errorStr)

def printErrorLog():
	global RuleFilePrintName,RuleFilePrintDic
	resultDic = {}
	resultDic["ErrorsFlag"] = False
	resultDic["ErrorsList"] = []
	splitFlag = False
	for fileName, printList in RuleFilePrintDic.items():
		if printList:
			if not splitFlag:
				print("################################\n")
				splitFlag = True
			logStr = "run Error RuleFile:{0}".format(os.path.split(fileName)[1])
			resultDic["ErrorsList"].append(logStr)
			print(logStr)
		for errorStr in printList:
			print(errorStr)
			resultDic["ErrorsList"].append(errorStr)

	resultDic["ErrorsFlag"] = splitFlag

	RuleFilePrintDic = {}
	RuleFilePrintName = None
	return resultDic

_LocalLongStrDic = None#查询表 查询中文字符串是否存在及位置
_LocalLongStrList = []#存储中文字符串
_LocalEmptyIndex = 0#Python列表可填入的序号
_LocalLongStrIndex = 0#Python列表长度
_LocalLongStrOldMap = None#映射 Lua文件名与字符串序号
_LocalLongStrNewMap = None#映射 Lua文件名与字符串序号
_CacheLocalLongStr = []
def InitLocalLongStr():
	global _LocalLongStrDic,_LocalLongStrOldMap,_LocalLongStrNewMap,_LocalLongStrList,_LocalEmptyIndex,_LocalLongStrIndex,DefaultTargetLuaFolder
	initLuaPath = os.path.join(os.getcwd(),DefaultTargetLuaFolder,"config.lua")
	luaContent = ""
	# #为保持生成数据一致 临时先删除文件再重新生成
	# if os.path.exists(initLuaPath):
	# 	os.remove(initLuaPath)
	if not os.path.exists(initLuaPath):
		with open(initLuaPath,mode="w+",encoding="utf-8",errors="ignore") as f:
			initContent = """-- luaTable表名 对应的rule中target字段所指LuaData文件
LuaData = LuaData or {}

LuaData.TableMapRequire = {
}

LuaData.LocalLongStrList = {
}

LuaData.FileMapStrIndexList = {
}
"""
			f.write(initContent)
	with open(initLuaPath,mode="r",encoding="utf-8",errors="ignore") as f:
		for line in f:
			luaContent = luaContent + line

	_LocalLongStrDic = {}
	_LocalLongStrList = []
	_LocalLongStrOldMap = {}
	_LocalLongStrNewMap = {}
	_LocalEmptyIndex = 0
	_LocalLongStrIndex = 0
	ResetCacheLocalLongStr(False)

	luaLocalLongStr = "LuaData.LocalLongStrList = {\n"
	startPos = luaContent.find(luaLocalLongStr)
	endPos = len(luaContent)
	if startPos != -1:#更新  去除旧数据
		posTuple = GetBracketRange(luaContent[startPos:],"{","}")#寻找OriginTable
		endPos = posTuple[1]+startPos
		startPos = posTuple[0]+startPos
		oldLuaContent = luaContent[startPos+1:endPos-1]
		# oldLuaContent = re.sub("[\t\n]","",oldLuaContent)
		# _LocalLongStrList = oldLuaContent.split(",")
		# if _LocalLongStrList[0] == "":
		# 	_LocalLongStrList = []
		_LocalLongStrList = re.findall("\t\[\d+\] = (.*?),?\n",oldLuaContent)
		_LocalEmptyIndex = None
		for index,longStr in enumerate(_LocalLongStrList):
			if longStr[0] == "\"":#字符串
				_LocalLongStrDic[longStr[1:-1]] = index+1
				_LocalLongStrList[index] = longStr[1:-1]
			else:
				_LocalLongStrList[index] = False
				if _LocalEmptyIndex is None:
					_LocalEmptyIndex = index
	_LocalLongStrIndex = len(_LocalLongStrList)
	if _LocalEmptyIndex is None:
		_LocalEmptyIndex = _LocalLongStrIndex

	fileMapStr = "LuaData.FileMapStrIndexList = {\n"
	startPos = luaContent.find(fileMapStr)
	endPos = len(luaContent)
	if startPos != -1:
		posTuple = GetBracketRange(luaContent[startPos:],"{","}")#寻找OriginTable
		endPos = posTuple[1]+startPos
		startPos = posTuple[0]+startPos
		oldLuaContent = luaContent[startPos+1:endPos-1]
		kvList = re.findall("\[\"(.*?)\"\] = \{(.*?)\},?",oldLuaContent)
		for kvTuple in kvList:
			k = kvTuple[0]
			v = kvTuple[1]
			indexList = v.split(",")
			_LocalLongStrOldMap[k] = [int(x) for x in indexList]

def LocalLongStr(longStr,fileName):
	global _LocalLongStrDic,_LocalLongStrList,_LocalLongStrNewMap,_LocalEmptyIndex,_LocalLongStrIndex
	if _LocalLongStrDic is None:
		# return "\"{0}\"".format(longStr)#临时去除 中文字符优化
		InitLocalLongStr()
	indexList = _LocalLongStrNewMap.get(fileName,[])
	strIndex = _LocalLongStrDic.get(longStr)
	if strIndex is not None:
		if strIndex not in indexList:
			indexList.append(strIndex)
		_LocalLongStrNewMap[fileName] = indexList
		return "LuaData.LocalLongStrList[{0}]".format(strIndex)
	else:
		if _LocalEmptyIndex < _LocalLongStrIndex:#存在空位
			strIndex = _LocalEmptyIndex+1
			_LocalLongStrDic[longStr] = strIndex
			indexList.append(strIndex)
			_LocalLongStrList[_LocalEmptyIndex] = longStr
			nextIndex = _LocalEmptyIndex+1
			_LocalEmptyIndex = _LocalLongStrIndex
			for i in range(nextIndex,_LocalLongStrIndex):
				if _LocalLongStrList[i] is False:
					_LocalEmptyIndex = i
					# print("Next _LocalEmptyIndex",_LocalEmptyIndex)
					break
		else:#_LocalEmptyIndex == _LocalLongStrIndex
			strIndex = _LocalEmptyIndex+1
			_LocalLongStrDic[longStr] = strIndex
			indexList.append(strIndex)
			_LocalLongStrList.append(longStr)
			_LocalLongStrIndex+=1
			_LocalEmptyIndex = _LocalLongStrIndex
		_LocalLongStrNewMap[fileName] = indexList
		return "LuaData.LocalLongStrList[{0}]".format(strIndex)

# isAll 去掉该标识了
def UpdateLocalLongStr(isAll):
	global _LocalLongStrDic,_LocalLongStrOldMap,_LocalLongStrNewMap,_LocalLongStrList,_LocalEmptyIndex,_LocalLongStrIndex,DefaultTargetLuaFolder
	if _LocalLongStrDic is None:
		return
	initLuaPath = os.path.join(os.getcwd(),DefaultTargetLuaFolder,"config.lua")
	luaContent = ""
	with open(initLuaPath,mode="r",encoding="utf-8",errors="ignore") as f:
		for line in f:
			luaContent = luaContent + line

	luaHoldStrDic = {}#查询字符串是否仍使用
	LocalLongStrMap = {}
	isAll = False#屏蔽该标识
	if isAll:
		_LocalLongStrOldMap = _LocalLongStrNewMap
		LocalLongStrMap = _LocalLongStrNewMap
	else:
		for fileName,indexList in _LocalLongStrNewMap.items():
			_LocalLongStrOldMap[fileName] = indexList
		LocalLongStrMap = _LocalLongStrOldMap
	_LocalLongStrNewMap = {}

	for indexList in LocalLongStrMap.values():
		for index in indexList:
			luaHoldStrDic[index] = True

	_LocalEmptyIndex = None
	for i,longStr in enumerate(_LocalLongStrList):
		if longStr and luaHoldStrDic.get(i+1) is None:#移除不再使用的字符串
			_LocalLongStrList[i] = False
			_LocalLongStrDic.pop(longStr)
		if _LocalEmptyIndex is None and _LocalLongStrList[i] is False:
			_LocalEmptyIndex = i
	if _LocalEmptyIndex is None:
		_LocalEmptyIndex = _LocalLongStrIndex

	luaLocalLongStr = "LuaData.LocalLongStrList = {\n"
	#新增
	NewContent = luaLocalLongStr
	firstData = True
	rowStr = ""
	for i,longStr in enumerate(_LocalLongStrList):
		if not firstData:
			rowStr = rowStr + ",\n"
		else:
			firstData = False
		if longStr is False:
			rowStr = rowStr + "\t[{0}] = false".format(i+1)
		else:
			rowStr = rowStr + "\t[{0}] = \"{1}\"".format(i+1,longStr)
	rowStr = rowStr + "\n}\n"
	NewContent = NewContent + rowStr

	startPos = luaContent.find(luaLocalLongStr)
	endPos = len(luaContent)
	if startPos != -1:#更新  去除旧数据
		posTuple = GetBracketRange(luaContent[startPos:],"{","}")#寻找OriginTable
		endPos = posTuple[1]+startPos+1#+1去除\n
		luaContent = luaContent[:startPos] + NewContent + luaContent[endPos:]
	else:
		luaContent = luaContent + "\n" + NewContent

	fileMapStr = "LuaData.FileMapStrIndexList = {\n"
	#新增
	NewContent = fileMapStr
	firstData = True
	rowStr = ""
	# list=[0 for x in range(0,10)]
	for fileName,indexList in LocalLongStrMap.items():
		if not firstData:
			rowStr = rowStr + ",\n"
		else:
			firstData = False

		rowStr = rowStr + "\t[\"{0}\"] = ".format(fileName)
		rowStr = rowStr + "{"
		firstIndex = True
		for index in indexList:
			if not firstIndex:
				rowStr = rowStr + ","
			else:
				firstIndex = False
			rowStr = rowStr + str(index)
		rowStr = rowStr + "}"
	rowStr = rowStr + "\n}\n"
	NewContent = NewContent + rowStr

	startPos = luaContent.find(fileMapStr)
	endPos = len(luaContent)
	if startPos != -1:#更新  去除旧数据
		posTuple = GetBracketRange(luaContent[startPos:],"{","}")#寻找OriginTable
		endPos = posTuple[1]+startPos+1#+1去除\n
		luaContent = luaContent[:startPos] + NewContent + luaContent[endPos:]
	else:
		luaContent = luaContent + "\n" + NewContent

	with open(initLuaPath,mode="w+",encoding="utf-8",errors="ignore") as f:
		f.write(luaContent)

def ResetCacheLocalLongStr(bReset):
	global _CacheLocalLongStr,_LocalLongStrDic,_LocalLongStrOldMap,_LocalLongStrNewMap,_LocalLongStrList,_LocalEmptyIndex,_LocalLongStrIndex
	# print("ResetCacheLocalLongStr bReset",bReset)
	if bReset:
		_LocalLongStrDic = copy.deepcopy(_CacheLocalLongStr[0])
		_LocalLongStrList = copy.deepcopy(_CacheLocalLongStr[1])
		_LocalLongStrOldMap = copy.deepcopy(_CacheLocalLongStr[2])
		_LocalLongStrNewMap = copy.deepcopy(_CacheLocalLongStr[3])
		_LocalEmptyIndex = _CacheLocalLongStr[4]
		print(347, _LocalEmptyIndex)
		_LocalLongStrIndex = _CacheLocalLongStr[5]
	else:
		# 顺序很重要
		_CacheLocalLongStr = []
		_CacheLocalLongStr.append(copy.deepcopy(_LocalLongStrDic))
		_CacheLocalLongStr.append(copy.deepcopy(_LocalLongStrList))
		_CacheLocalLongStr.append(copy.deepcopy(_LocalLongStrOldMap))
		_CacheLocalLongStr.append(copy.deepcopy(_LocalLongStrNewMap))
		_CacheLocalLongStr.append(_LocalEmptyIndex)
		_CacheLocalLongStr.append(_LocalLongStrIndex)

def UpdateLuaRequire(luaTableRequireDic):
	global DefaultTargetLuaFolder
	initLuaPath = os.path.join(os.getcwd(),DefaultTargetLuaFolder,"config.lua")
	luaContent = ""
	with open(initLuaPath,mode="r",encoding="utf-8",errors="ignore") as f:
		for line in f:
			luaContent = luaContent + line

	luaRequireTableStr = "LuaData.TableMapRequire = {\n"
	startPos = luaContent.find(luaRequireTableStr)
	if startPos != -1:
		posTuple = GetBracketRange(luaContent[startPos:],"{","}")
		endPos = posTuple[1]+startPos
		startPos = posTuple[0]+startPos

		tableContent = luaContent[startPos+2:endPos-1]#去除前"{\n" 后"}"
		lastLuaTableName = ""#用于去除 _GetRowDataByKey
		for luaTableName,luaFileName in luaTableRequireDic.items():
			if len(luaTableName) <= 16 or luaTableName[-16:] != "_GetRowDataByKey":
				result = re.search("(\t"+lastLuaTableName+"_GetRowDataByKey"+" = \".*?\",?\n)",tableContent)
				if result:#更新  去除旧数据
					searchTuple = result.span()
					oldStartPos = searchTuple[0]
					oldEndPos = searchTuple[1]
					tableContent = tableContent[:oldStartPos] + tableContent[oldEndPos:]
				lastLuaTableName = luaTableName
			else:
				lastLuaTableName = ""

			NewContent = "\t{0} = \"{1}\",\n".format(luaTableName,luaFileName)
			result = re.search("(\t"+luaTableName+" = \".*?\",?\n)",tableContent)
			if result:#更新  去除旧数据
				searchTuple = result.span()
				oldStartPos = searchTuple[0]
				oldEndPos = searchTuple[1]
				tableContent = tableContent[:oldStartPos] + NewContent + tableContent[oldEndPos:]
			else:
				if tableContent == "":#第一行
					tableContent = tableContent + NewContent
				elif tableContent[-2:] == ",\n":
					tableContent = tableContent + NewContent
				elif tableContent[-1] == "\n":
					tableContent = tableContent[:-1] + ",\n" + NewContent
				else:
					printError("tableContent errors {0}".format(tableContent))

		if tableContent[-2:] == ",\n":#去除最后一项多余的","
			tableContent = tableContent[:-2] + "\n"
		tableContent = "{\n" + tableContent + "}"
		luaContent = luaContent[:startPos] + tableContent + luaContent[endPos:]
	else:
		printError("init.lua not find TableMapRequire")
		return

	with open(initLuaPath,mode="w+",encoding="utf-8",errors="ignore") as f:
		f.write(luaContent)

class RuleFile:
	def __init__(self, ruleFilePath):
		self.keyDic = {}#规则文件 关键字信息字典
		self.keysMap = {}#表结构  (序号,字段,字段类型)
		self.ruleFilePath = ruleFilePath

		self.targetLua = None#生成配置表的Lua名字 带后缀
		self.targetLuaPath = None#生成配置表的Lua路径
		self.configList = {}#配置表列表
		self.tableList = {}#Lua表列表
		self.luaTableDic = {}#可访问的Lua表名

	def InitRule(self):
		spaceRe = re.compile("\s")
		content = ""
		setPrintFile(self.ruleFilePath)
		with open(self.ruleFilePath,mode="r",encoding="utf-8",errors="ignore") as f:
			for line in f:
				line = line.partition("//")[0]#删除注释
				# line = spaceRe.sub("",line)#去掉空白符   分隔符可能为空格
				if len(line) == 0: continue
				content = content+line

		result = re.search("/\*(.*?)\*/", content, re.DOTALL)
		if result:#删除注释
			spanTuple = result.span()
			content = content[:spanTuple[0]]+content[spanTuple[1]:]
		posTuple = GetBracketRange(content,"{","}")
		startPos = posTuple[0]
		endPos = posTuple[1]
		content = content[startPos:endPos]

		try:
			self.keyDic = json.loads(content)
		except Exception as e:
			printError("json loads rule File wrong:")
			printError("check rule File content in https://www.json.cn/")
			return

		self.targetLua = self.keyDic.get("target")
		if self.targetLua:
			global DefaultTargetLuaFolder
			self.targetLuaPath = os.path.join(os.getcwd(),DefaultTargetLuaFolder,self.targetLua)
			# print("targetLuaPath:",self.targetLuaPath)
		else:
			printError("not find targetLuaPath")
			return

		configList = self.keyDic.get("ConfigList")
		if configList:
			for configName,config in configList.items():
				if not config.get("Path"):
					printError("not find config:{0} path".format(configName))
					return
				config["Mode"]="KV"#现configMode不可变为KV
				config["MainKeys"]=[]#现MainKeys不可变为空表
				#config.setdefault("MainKeys",[])#默认值
				allKeys = config.get("AllKeys")
				for v in allKeys:
					v.setdefault("type","String")#默认值
				config["AllKeys"] = allKeys
				self.configList[configName] = config
				#self.luaTableDic[configName] = self.targetLua[:-4]#去除后缀".lua"
		else:
			printError("not find ConfigList in rule File:{0}".format(self.ruleFilePath))
			return

		tableList = self.keyDic.get("TableList")
		if tableList:
			for tableName,table in tableList.items():
				table.setdefault("Mode","KV")#默认值
				self.tableList[tableName] = table
				self.luaTableDic[tableName] = self.targetLua[:-4]#去除后缀".lua"
				if table.get("MainKeys"):
					self.luaTableDic[tableName+"_GetRowDataByKey"] = self.targetLua[:-4]#去除后缀".lua"

	def Update(self):
		if self.targetLuaPath is None:
			# printError("not find targetLuaPath")
			return
		if not os.path.exists(self.targetLuaPath):
			with open(self.targetLuaPath,mode="w",encoding="utf-8",errors="ignore") as f:
				f.write("local LuaData = LuaData\n")
		else:
			with open(self.targetLuaPath,mode="r",encoding="utf-8",errors="ignore") as f:
				line = f.readline()
				if line != "local LuaData = LuaData\n":
					printError("targetLua first line default is:\"local LuaData = LuaData\\n\"")
					return
		self.configOriginDataDic = {}
		self.configMainKeyValueDic = {}
		self.csvOriginDataDic = {}
		self.luaContent = ""
		with open(self.targetLuaPath,mode="r",encoding="utf-8",errors="ignore") as f:
			for line in f:
				self.luaContent = self.luaContent + line
		for configName in self.configList:
			if self.UpdateConfig(configName) is None:
				return
		for tableName in self.tableList:
			if self.UpdateTable(tableName) is None:
				return
		with open(self.targetLuaPath,mode="w+",encoding="utf-8",errors="ignore") as f:
			f.write(self.luaContent)
		UpdateLuaRequire(self.luaTableDic)
		return True

	def UpdateConfig(self,configName):
		configDic = self.configList[configName]
		originPath = configDic["Path"]
		global DefaultCSVFolder
		csvPath = os.path.join(os.getcwd(),DefaultCSVFolder,originPath)
		dataTuple = self.csvOriginDataDic.get(originPath,readCSV(csvPath))
		keyIndexDic = dataTuple[0]
		dataMatrix = dataTuple[1]
		# dataMatrix = LocalChinessStr(dataMatrix)
		errorFileInfo = "ruleFileName:{0}\ncsvFileName:{1}\n".format(os.path.basename(self.ruleFilePath), originPath)

		allKeys = configDic["AllKeys"]
		configKeyList = []#关键字的序号
		configKeyIndexDic = {}#关键字的名字映射序号
		for i,keyDic in enumerate(allKeys):
			keyName = keyDic["name"]
			keyType = keyDic["type"]
			if keyIndexDic.get(keyName) is None:
				printError("{0} can't find keyName:{1}".format(errorFileInfo, keyName))
				return
			index = keyIndexDic[keyName]
			configKeyList.append(keyName)
			configKeyIndexDic[keyName] = i
			for rowDataList in dataMatrix:
				listLen = len(rowDataList)
				if listLen == 0:
					return
				if index >= listLen:
					printError("{0} can't find {1} rowData in {2}".format(errorFileInfo, keyName, rowDataList))
					return
				try:
					if keyType == "Number":
						if rowDataList[index] == "":#数值类型 空格代表0
							rowDataList[index] = 0
						else:
							rowDataList[index] = int(rowDataList[index])
					elif keyType == "Float":
						if rowDataList[index] == "":#数值类型 空格代表0
							rowDataList[index] = 0.0
						else:
							rowDataList[index] = float(rowDataList[index])
					elif keyType == "Bool":
						if rowDataList[index] == "True" or rowDataList[index] == "true":
							rowDataList[index] = True#"true"
						elif rowDataList[index] == "False" or rowDataList[index] == "false":
							rowDataList[index] = False#"false"
						else:							
							printError("{0} data:{1} can't convert to type:{2} of key:{3}, support:True、true、False、false".format(errorFileInfo,rowDataList[index],keyType,keyName))
							rowDataList[index] = False
					elif keyType == "List":
						listSplit = keyDic.get("ListSplit",",")
						if rowDataList[index] != "":
							splitContent = rowDataList[index]
							length = len(splitContent)
							rangeL = keyDic.get("RangeL",0)
							rangeR = keyDic.get("RangeR",length)
							try:
								splitContent = splitContent[rangeL:rangeR]
							except Exception as e:
								printError("{0} list data:{1} can't getRange[{2}:{3}] to split by \"{2}\" of key:{3} ".format(errorFileInfo,rowDataList[index],rangeL,rangeR,listSplit,keyName))
								return
							if splitContent != "":
								rowDataList[index] = tuple(splitContent.split(listSplit))#计算默认值时不支持list做key
							else:
								rowDataList[index] = tuple([])
						else:
							rowDataList[index] = tuple([])
					elif keyType == "TagName":
						rowDataList[index] = GetTagNameString(rowDataList[index])
					elif keyType == "IconPath":
						rowDataList[index] = GetAssetIconPath(rowDataList[index])
					elif keyType == "GameplayTags":
						rowDataList[index] = tuple(GetTagsList(rowDataList[index]))
				except Exception as e:
					printError("{0} data:{1} can't convert to type:{2} of key:{3}".format(errorFileInfo,rowDataList[index],keyType,keyName))
					return

		configDataMatrix = []
		for rowDataList in dataMatrix:
			configRow = []
			for key in configKeyList:
				index = keyIndexDic[key]
				configRow.append(rowDataList[index])
			configDataMatrix.append(configRow)

		mainKeys = configDic["MainKeys"]
		mainKeyIndexList = []
		for mainKey in mainKeys:
			mainKeyIndexList.append(configKeyIndexDic[mainKey])

		configMode = configDic["Mode"]
		self.configOriginDataDic[configName] = (configKeyList,configKeyIndexDic,configDataMatrix,configMode)
		defaultMeta = self.UpdateLuaConfigDefault(configName,configDataMatrix)
		self.UpdateLuaConfig(configName,mainKeyIndexList,defaultMeta)
		return True

	def UpdateLuaConfigDefault(self,configName,configDataMatrix):
		defaultMeta = []
		matrix = {}
		for rowDataList in configDataMatrix:
			for index,value in enumerate(rowDataList):
				colDic = matrix.get(index,{})
				num = colDic.get(value,0)
				num = num + 1
				colDic[value] = num
				matrix[index] = colDic

		for colDic in matrix.values():
			maxNum = 0
			insertValue = ""
			for value,num in colDic.items():
				if num > maxNum:
					maxNum = num
					insertValue = value

			defaultMeta.append(insertValue)

		luaOrignDefaultMetaStr = "LuaData.{0}_DefaultMeta".format(configName)+" = {\n"
		#新增
		NewContent = luaOrignDefaultMetaStr
		firstData = True
		rowStr = ""
		for defaultValue in defaultMeta:
			if not firstData:
				rowStr = rowStr + ",\n"
			else:
				firstData = False
			if type(defaultValue) is str:
				if isContainChinese(defaultValue):
					rowStr = rowStr + "\t{0}".format(LocalLongStr(defaultValue,self.targetLua))
				else:
					rowStr = rowStr + "\t\"{0}\"".format(defaultValue)
			elif type(defaultValue) is tuple:
				listStr = ""
				for v in defaultValue:
					listStr+="\"{0}\",".format(v)
				if len(listStr) > 0:#listStr[-1] == ","
					listStr = listStr[:-1]
				rowStr = rowStr + "\t{" + listStr+"}"
			elif type(defaultValue) is bool:
				if defaultValue:
					rowStr = rowStr + "\ttrue"
				else:
					rowStr = rowStr + "\tfalse"
			else:
				rowStr = rowStr + "\t{0}".format(defaultValue)
		rowStr = rowStr + "\n}\n"
		NewContent = NewContent + rowStr

		startPos = self.luaContent.find(luaOrignDefaultMetaStr)
		endPos = len(self.luaContent)
		if startPos != -1:#更新  去除旧数据
			posTuple = GetBracketRange(self.luaContent[startPos:],"{","}")#寻找OriginTable
			endPos = posTuple[1]+startPos+1#+1去除\n
			self.luaContent = self.luaContent[:startPos] + NewContent + self.luaContent[endPos:]
		else:
			self.luaContent = self.luaContent + "\n" + NewContent

		return defaultMeta

	# 更新Config相关的Lua代码
	def UpdateLuaConfig(self,configName,mainKeyIndexList,defaultMeta):
		luaOrignStr = "LuaData.{0}".format(configName)+" = {\n"
		#新增
		NewContent = luaOrignStr
		configTupe = self.configOriginDataDic[configName]
		configKeyList = configTupe[0]
		configDataMatrix = configTupe[2]
		configMode = configTupe[3]
		configMainKeyValue = self.configMainKeyValueDic.get(configName,[])
		rowStr = ""
		firstRow = True
		isIpair = True
		for i,rowDataList in enumerate(configDataMatrix):
			keyValue = ""
			firstFlag = True
			for keyIndex in mainKeyIndexList:
				if firstFlag:
					firstFlag = False
					keyValue = rowDataList[keyIndex]
				else:
					keyValue = str(keyValue)+"_"+str(rowDataList[keyIndex])

			if not firstRow:
				rowStr = rowStr + ",\n"
			else:
				firstRow = False

			if not firstFlag:#存在MainKeys字段时
				if type(keyValue) is str:
					keyValue = "\"{0}\"".format(keyValue)
				rowStr = rowStr + "\t[{0}] = ".format(keyValue)+"{"
				configMainKeyValue.append(keyValue)
				isIpair = False
			else:
				rowStr = rowStr + "\t{"
				configMainKeyValue.append(i+1)#Python列表从0开始 Lua数组从1开始
				isIpair = True

			firstData = True
			numBreakFlag = False
			for index,rowData in enumerate(rowDataList):
				if defaultMeta[index] == rowData:#跳过默认值
					numBreakFlag = True
					continue
				varFlag = False
				if type(rowData) is str and isContainChinese(rowData):
					rowData = LocalLongStr(rowData,self.targetLua)
					varFlag = True
				if not firstData:
					rowStr = rowStr + ","
				else:
					firstData = False
				if configMode == "KV":
					# rowStr = rowStr + configKeyList[index] + "="
					if numBreakFlag:#数组被打断
						rowStr = rowStr + "[" + str(index+1) + "]="
				if type(rowData) is int:
					rowStr = rowStr + str(rowData)
				elif type(rowData) is tuple:
					listStr = ""
					for v in rowData:
						listStr+="\"{0}\",".format(v)
					if len(listStr) > 0:#listStr[-1] == ","
						listStr = listStr[:-1]
					rowStr = rowStr + "{" + listStr +"}"
				elif type(rowData) is bool:
					if rowData:
						rowStr = rowStr + "true"
					else:
						rowStr = rowStr + "false"
				else:
					if varFlag:
						rowStr = rowStr + rowData
					else:
						rowStr = rowStr + "\"{0}\"".format(rowData)
			rowStr = rowStr + "}"
		rowStr = rowStr + "\n}\n"
		NewContent = NewContent + rowStr
		self.configMainKeyValueDic[configName] = configMainKeyValue

		startPos = self.luaContent.find(luaOrignStr)
		endPos = len(self.luaContent)
		if startPos != -1:#更新  去除旧数据
			posTuple = GetBracketRange(self.luaContent[startPos:],"{","}")#寻找OriginTable
			endPos = posTuple[1]+startPos+1#+1去除\n
			self.luaContent = self.luaContent[:startPos] + NewContent + self.luaContent[endPos:]
		else:
			self.luaContent = self.luaContent + "\n" + NewContent

		#设置元表
		metaMatchStr = "local meta = {__index="+"LuaData.{0}_DefaultMeta".format(configName)+"}\n"
		metaLuaStr = metaMatchStr
		if isIpair:
			metaLuaStr=metaLuaStr+"for i,v in ipairs(LuaData.{0}) do\n".format(configName)
		else:
			metaLuaStr=metaLuaStr+"for i,v in pairs(LuaData.{0}) do\n".format(configName)
		metaLuaStr=metaLuaStr+"\tsetmetatable(v,meta)\nend\n"

		result = re.search("{0}(.*?)end\n".format(metaMatchStr),self.luaContent,re.DOTALL)
		if result:
			posTuple = result.span()
			startPos = posTuple[0]
			endPos = posTuple[1]
			self.luaContent = self.luaContent[:startPos] + metaLuaStr + self.luaContent[endPos:]
		else:
			self.luaContent = self.luaContent + "\n" + metaLuaStr

	def UpdateTable(self,tableName):
		tableDic = self.tableList[tableName]
		origin = tableDic.get("Origin")
		mainKeys = tableDic.get("MainKeys",[])
		tableMode = tableDic.get("Mode","Array")
		allKeys = tableDic.get("AllKeys")

		if self.configOriginDataDic.get(origin) is None:
			return

		originDataTuple = self.configOriginDataDic[origin]
		configKeyList = originDataTuple[0]
		configKeyIndexDic = originDataTuple[1]
		configDataMatrix = originDataTuple[2]
		configMode = originDataTuple[3]

		tableKeyList = []
		if allKeys == "all":
			tableKeyList = configKeyList
		elif type(allKeys) is list:
			tableKeyList = allKeys
			for tableKey in tableKeyList:
				if configKeyIndexDic.get(tableKey) is None:
					printError("can't find tableKey:{0} in AllKeys of {1}".format(tableKey, origin))
					return
		else:
			return
		
		mainKeyIndexList = []
		for mainKey in mainKeys:
		# for i,mainKey in mainKeys.items():
			try:
				mainKeyIndexList.append(configKeyIndexDic[mainKey])
			except Exception as e:
				printError("can't find mainKey:{0} in AllKeys of {1}".format(mainKey, origin))
				return
		if len(mainKeyIndexList) > 0:
			self.UpdateLuaTable(tableName,tableKeyList,origin,configMode,configKeyIndexDic,False)
		else:
			self.UpdateLuaTable(tableName,tableKeyList,origin,configMode,configKeyIndexDic,True)
		self.UpdateLuaTableMainKey(tableName,tableMode,mainKeyIndexList,origin,configDataMatrix)
		return True

	# 更新Table相关的Lua代码
	def UpdateLuaTable(self,tableName,tableKeyList,configName,configMode,configKeyIndexDic,isIpair):
		luaOrignTableKeyMapStr = "LuaData.{0}_KeyMap".format(tableName)+" = {\n"
		#新增
		NewContent = luaOrignTableKeyMapStr
		firstData = True
		rowStr = ""
		for tableKey in tableKeyList:
			if not firstData:
				rowStr = rowStr + ",\n"
			else:
				firstData = False

			#configMode 现在默认都为KV 但元表采用数字做key
			if tableKey == "---":
				rowStr = rowStr + "\t[\"---\"] = {0}".format(configKeyIndexDic[tableKey]+1)
			else:
				rowStr = rowStr + "\t{0} = {1}".format(tableKey,configKeyIndexDic[tableKey]+1)#Python列表从0开始 Lua数组从1开始
			# if configMode == "KV":#KV模式采用字段名做key Array模式采用数字做key
			# 	rowStr = rowStr + "\t{0} = \"{0}\"".format(tableKey)
			# else:
			# 	rowStr = rowStr + "\t{0} = {1}".format(tableKey,configKeyIndexDic[tableKey]+1)#Python列表从0开始 Lua数组从1开始

		rowStr = rowStr + "\n}\n"
		NewContent = NewContent + rowStr

		startPos = self.luaContent.find(luaOrignTableKeyMapStr)
		endPos = len(self.luaContent)
		if startPos != -1:#更新  去除旧数据KeyMap
			posTuple = GetBracketRange(self.luaContent[startPos:],"{","}")#寻找OriginTable
			endPos = posTuple[1]+startPos+1#+1去除\n
			self.luaContent = self.luaContent[:startPos] + NewContent + self.luaContent[endPos:]
		else:
			self.luaContent = self.luaContent +"\n"+ NewContent


		# 设置元表
		tableLuaStr=""
		tableLuaStr=tableLuaStr+"LuaData.{0} = ".format(tableName) + "{}\n"
		isIpair = True# configName现固定为顺序表 tableName也固定为顺序表
		if isIpair:
			tableLuaStr=tableLuaStr+"for i,v in ipairs(LuaData.{0}) do\n".format(configName)
		else:
			tableLuaStr=tableLuaStr+"for k,v in pairs(LuaData.{0}) do\n".format(configName)
		tableLuaStr=tableLuaStr+"\tlocal temp = setmetatable({__originMeta=v},{__index=LuaData.getValueByKey,"+"__keyMap=LuaData.{0}_KeyMap".format(tableName)+"})\n"
		if isIpair:
			tableLuaStr=tableLuaStr+"\ttable.insert(LuaData.{0},temp)\n".format(tableName)
		else:
			tableLuaStr=tableLuaStr+"\tLuaData.{0}[k] = temp\n".format(tableName)
		tableLuaStr=tableLuaStr+"end\n"

		result = re.search("LuaData.{0} = .*?end\n".format(tableName),self.luaContent,re.DOTALL)
		if result:
			posTuple = result.span()
			startPos = posTuple[0]
			endPos = posTuple[1]
			self.luaContent = self.luaContent[:startPos] + tableLuaStr + self.luaContent[endPos:]
		else:
			self.luaContent = self.luaContent +"\n"+ tableLuaStr

	def UpdateLuaTableMainKey(self,tableName,tableMode,mainKeyIndexList,configName,configDataMatrix):
		mainKeyToRowIndex = {}
		if tableMode != "Array":
			for i,rowDataList in enumerate(configDataMatrix):
				keyValue = ""
				firstFlag = True
				for keyIndex in mainKeyIndexList:
					if firstFlag:
						firstFlag = False
						keyValue = rowDataList[keyIndex]
					else:
						keyValue = str(keyValue)+"_"+str(rowDataList[keyIndex])
				if not firstFlag:
					if tableMode == "KV":
						mainKeyToRowIndex[keyValue] = i
					elif tableMode == "KList":
						rowIndexList = mainKeyToRowIndex.get(keyValue,[])
						rowIndexList.append(i)
						mainKeyToRowIndex[keyValue] = rowIndexList

		luaOrignStr = "LuaData.{0}_GetRowDataByKey".format(tableName)+" = {\n"
		#新增
		NewContent = luaOrignStr
		firstData = True
		rowStr = ""
		configMainKeyValue = self.configMainKeyValueDic.get(configName,[])
		for keyValue,indexData in mainKeyToRowIndex.items():
			if not firstData:
				rowStr = rowStr + ",\n"
			else:
				firstData = False

			if type(keyValue) is str:
				rowStr = rowStr + "\t[\"{0}\"]=".format(keyValue)
			else:
				rowStr = rowStr + "\t[{0}]=".format(keyValue)

			if tableMode == "KV":
				mainKey = configMainKeyValue[indexData]
				rowStr = rowStr + "LuaData.{0}[{1}]".format(tableName,mainKey)#Python列表从0开始 Lua数组从1开始
			elif tableMode == "KList":
				rowStr = rowStr + "{"
				firstIndex = True
				for index in indexData:
					if not firstIndex:
						rowStr = rowStr + ","
					else:
						firstIndex = False
					mainKey = configMainKeyValue[index]
					rowStr = rowStr + "LuaData.{0}[{1}]".format(tableName,mainKey)#Python列表从0开始 Lua数组从1开始
				rowStr = rowStr + "}"

		rowStr = rowStr + "\n}\n"
		NewContent = NewContent + rowStr
		if firstData:#无数据
			NewContent = ""

		startPos = self.luaContent.find(luaOrignStr)
		endPos = len(self.luaContent)
		if startPos != -1:#更新  去除旧数据KeyMap
			posTuple = GetBracketRange(self.luaContent[startPos:],"{","}")#寻找OriginTable
			endPos = posTuple[1]+startPos+1#+1去除\n
			self.luaContent = self.luaContent[:startPos] + NewContent + self.luaContent[endPos:]
		else:
			if NewContent != "":
				self.luaContent = self.luaContent +"\n"+ NewContent

def isContainChinese(str):
	for c in str:
		if u'\u4e00' <= c <= u'\u9fff':
			return True
	return False

def getFilesByFolder(folder):
	folderPath = os.path.join(os.getcwd(),folder)
	filePathList = []
	for root,dirs,files in os.walk(folderPath):
		for file in files:
			filePathList.append(os.path.join(root,file))
	return filePathList

def readCSV(filePath):
	with open(filePath,mode="r",encoding="utf-8-sig",errors="ignore") as f:
		lineIndex = 0
		keyIndexDic = {}
		dataMatrix = []
		f_csv = csv.reader(f)
		for rowDataList in f_csv:
			lineIndex = lineIndex + 1
			if lineIndex == 1:
				for i,key in enumerate(rowDataList):
					keyIndexDic[key] = i
				continue
			if lineIndex == 2:#第二行默认为描述
				continue
			dataMatrix.append(rowDataList)

		return keyIndexDic,dataMatrix


#None 默认当前文件夹所有
def runFileCmd(filePath=None):
	if filePath is None:
		filePathList = getFilesByFolder(DefaultRuleFolder)
		for filePath in filePathList:
			if filePath[-5:] == ".json":
				print("find rule file:",os.path.split(filePath)[1])
				rule = RuleFile(filePath)
				rule.InitRule()
				if rule.Update() is None:
					ResetCacheLocalLongStr(True)
				else:
					ResetCacheLocalLongStr(False)
			else:
				# print("ignore file:{0}".format(filePath))
				pass
		UpdateLocalLongStr(True)
		return printErrorLog()
	else:
		folderPath = os.path.join(os.getcwd(),DefaultRuleFolder)
		if filePath[-5:] != ".json":
			filePath = filePath+".json"
			print("runFileCmd() filePath:",filePath)

		if os.path.exists(os.path.join(folderPath,filePath)):
			print("find rule file:",os.path.split(filePath)[1])
			rule = RuleFile(filePath)
			rule.InitRule()
			if rule.Update() is None:
				ResetCacheLocalLongStr(True)
			else:
				ResetCacheLocalLongStr(False)
		else:
			print("can't find rule file:{0}".format(filePath))
			pass
		UpdateLocalLongStr(False)
		return printErrorLog()

def main(*args,**kwargs):
	global DefaultCSVFolder
	print("todo   input path")
	print("run script workpath=getcwd():",os.getcwd())
	print("args:",args)
	# 为区分流水线与双击bat批处理  设置两种入口
	result = {}
	if len(args) >= 2:
		# 流水线(脚本间接调用)入口  暂未处理传入参数
		filePath = None
		if args[1] == "csvPath":
			DefaultCSVFolder = args[2]
			print("csvPath:",os.path.join(os.getcwd(),DefaultCSVFolder))
		elif args[1] == "update":
			filePath = args[2]
		try:
			result = runFileCmd(filePath)
		except Exception as e:
			print("impossible errors !!! runFileCmd() capture a error:", e)
	else:
		# bat批处理双击  入口
		# try:
			result = inputRun()
		# except Exception as e:
		# 	print("impossible errors !!! inputRun() capture a error:", e)
	if result and result["ErrorsFlag"]:
		print("auto quit after 5 seconds ")
		time.sleep(5)
	return result

def inputRun():
	return runFileCmd()
# 	global DefaultRuleFolder

# 	commandHelpStr = """\ncommand help:
# >>update
# update all ruleFiles
# >>update ruleFileName
# update ruleFile all configName
# """
# 	runFileCmd()#默认无参数进入 更新全部文件  临时
# 	print(commandHelpStr)
# 	while True:
# 		command = input("run command or 空字符退出:")
# 		if command == "":
# 			break
# 		else:
# 			# print("command:\"{0}\"".format(command))
# 			args = re.split("\s+",command)
# 			argsNum = len(args)
# 			if args[0] != "update":
# 				print("args[0]:\"{0}\"".format(args[0]))
# 				print(commandHelpStr)
# 				continue
# 			if argsNum == 1:
# 				runFileCmd()#None 默认当前文件夹所有
# 			elif argsNum == 2 and args[1] == "":# "update "会split成['update','']两个
# 				runFileCmd()#None 默认当前文件夹所有
# 			elif argsNum >= 2:
# 				filePath = args[1]
# 				runFileCmd(filePath)


if __name__ == "__main__":
	main(*sys.argv)

#excel表可以配置起始行
