import os
import re
import json
import csv
from Check import *
from main import *

DefaultCSVFolder = "..\\NZTrunk\\Documents\\csv"#读取的CSV文件夹路径
DefaultCheckRuleName = "CheckRule.json"

errorDic = []
errorState = None

LogTag = 0
LogLimitList = [
	# "Equal",
	# "Print",
	# "Equal",
	"csvIndex:",
]
def Log(logStr=""):
	flag = False
	for i,limitStr in enumerate(LogLimitList):
		if re.match(limitStr, logStr):
			flag = True
			break
	if LogLimitList and not flag:
		return

	global LogTag
	LogTag = (LogTag + 1)%10
	print("{0}\n{1}\n{0}".format(str(LogTag)*20,logStr))

def printError(errorStr):
	print(errorStr)
	errorDic.append(errorStr)

def getNodeLog(treeNode):
		csvName = treeNode.getCSVName()
		csvKeyList = treeNode.getCSVKeyList()
		return "<<{0} key:{1}>>".format(csvName,csvKeyList)

def readCSV(csvFolderPath, fileName, keyList):
	filePath = os.path.join(csvFolderPath, fileName)
	# Log("readCSV filePath:{0} fileName:{1} keyList:{2}".format(filePath, fileName, keyList))
	if not os.path.exists(filePath):
		printError("csv path:{0} is not exists!".format(filePath))
		return
	with open(filePath,mode="r",encoding="utf-8-sig",errors="ignore") as f:
	# with open(filePath,mode="r",encoding="utf-8-sig",errors="ignore") as f:
		lineIndex = 0
		keyIndexDic = {}
		dataMatrix = {}
		for key in keyList:
			dataMatrix.setdefault(key, [])

		f_csv = csv.reader(f)
		for rowDataList in f_csv:
			lineIndex = lineIndex + 1
			if lineIndex == 1:
				for i,key in enumerate(rowDataList):
					if dataMatrix.get(key) is not None:#空表和None的判断结果一样
						keyIndexDic[i] = key#后续值替换为dataMatrix.get(key)

				if len(keyIndexDic) != len(dataMatrix):
					values = keyIndexDic.values()
					for key in dataMatrix.keys():
						if key not in values:
							printError("can't find key:{0} in file:{1}".format(key,filePath))
					return
				else:
					for i,key in keyIndexDic.items():
						keyIndexDic[i] = dataMatrix.get(key)
			elif lineIndex != 2:#第二行默认为描述
				for i,value in enumerate(rowDataList):
					dataList = keyIndexDic.get(i)#空表和None的判断结果一样
					if dataList is not None:
						dataList.append(value)

		# print("readCSV dataMatrix",dataMatrix)
		return dataMatrix

class Rule:
	def __init__(self, checkRuleFilePath,csvFolderPath):
		self.ruleDic = {}

		self.checkRuleFilePath = checkRuleFilePath
		self.csvFolderPath = csvFolderPath
		Log("Init Rule checkRuleFilePath:{0} csvFolderPath:{1}".format(self.checkRuleFilePath, self.csvFolderPath))
		self.csvKeyCache = {}# csvIndex为key  查询csv的需要保存的key关键字
		self.csvNameCache = {}# csv文件名缓存(带后缀) csvIndex为key
		self.csvIndexMap = {}
		self.csvNameMap = {}
		self.csvDataMatrix = {}# 数据总表   两层字典 key为csvIndex:csvKey  value为keyValueList
		self.ruleTreeList = []# 检查树 列表

		self.opDic = {}#

		self.errorList = []#错误信息

	# 多关键字组合数据
	def getCSVKeyValueList(self,csvIndex,csvKeyList):
		# print("getCSVKeyValueList csvIndex:{0} csvKeyList:{1}".format(csvIndex,csvKeyList))
		csvData = self.csvDataMatrix.get(csvIndex)
		keyValueList = []
		if csvData:
			for csvKey in csvKeyList:
				# valueList = csvData.get(csvKey)
				valueList = self.getCSVFilterValueList(csvIndex,csvKey)
				if not valueList:
					printError("can't find csvKey:{0} in csvKeyList:{1} from csvIndex:{2} csv:{3}".format(csvKey,csvKeyList,csvIndex,csvName))
					return
				for index,value in enumerate(valueList):
					if len(keyValueList) == index:#第一列关键字数据
						keyValueList.append(value)
						# keyValueList[index] = value
					else:
						keyValueList[index] = keyValueList[index] + "_" + value
			if keyValueList:
				return keyValueList
			else:
				csvName = self.getCSVNameByIndex(csvIndex, "<None>")
				printError("can't find csvKeyList:{0} in csvIndex:{1} csv:{2}".format(csvKeyList,csvIndex,csvName))
		else:
			csvName = self.getCSVNameByIndex(csvIndex, "<None>")
			printError("can't find csvIndex:{0} csv:{1}".format(csvIndex,csvName))

	def initRule(self):
		content = ""
		# CheckRuleFilePath = os.path.join(os.getcwd(),"CheckRule.txt")
		# print("initRule filePath:",CheckRuleFilePath)
		if not os.path.exists(self.checkRuleFilePath):
			printError("CheckRulePath:{0} is not exists".format(self.checkRuleFilePath))
			return

		with open(self.checkRuleFilePath,mode="r",encoding="utf-8",errors="ignore") as f:
				for line in f:
					line = line.partition("//")[0]#删除注释
					if len(line) == 0: continue
					content = content+line

		result = re.search("/\*(.*?)\*/", content, re.DOTALL)#删除/**/注释
		if result:
			spanTuple = result.span()
			content = content[:spanTuple[0]]+content[spanTuple[1]:]

		try:
			self.ruleDic = json.loads(content)
		except Exception as e:
			printError("json loads rule File wrong:{0}".format(e))
			printError("check rule File content in https://www.json.cn/")
			return

		self.initCSVList()
		self.initCSVDataMatrix()
		self.showData()

	def initCSVList(self):
		self.csvNameCache = {}
		# csvMap = self.ruleDic.get("CSVMap", {})
		# for csvIndex, csvName in csvMap.items():
		# 	self.csvNameCache[csvIndex] = csvName+".csv"
		# 	self.csvIndexMap[csvIndex] = csvName
		# 	self.csvNameMap[csvName] = csvIndex
		csvMapList = self.ruleDic.get("CSVMap", [])
		for tupleList in csvMapList:
			csvIndex = str(tupleList[0])
			csvName = tupleList[1]
			self.csvNameCache[csvIndex] = csvName+".csv"
			self.csvIndexMap[csvIndex] = csvName
			self.csvNameMap[csvName] = csvIndex

		self.csvKeyRuleDicMatrix = {}
		csvKeyRule = self.ruleDic.get("CSVKeyRule", {})
		for csvName,keysRule in csvKeyRule.items():
			csvIndex = self.csvNameMap[csvName]
			keyRuleDic = {}
			for keyRule in keysRule:
				keyName = keyRule.get("name")
				keyRuleDic[keyName] = keyRule
			self.csvKeyRuleDicMatrix[csvIndex] = keyRuleDic
		Log("csvKeyRuleDicMatrix:{0}".format(self.csvKeyRuleDicMatrix))

		self.csvKeyCache = {}
		#列规则列表
		csvRuleList = self.ruleDic.get("CSVColRuleList", [])
		for treeData in csvRuleList:
			for linkData in treeData:
				csvKeyList = None
				for v in linkData:
					# if v.isdigit():
					if type(v) == int:
						# csvIndex = v#注意这里索引采用数字的字符串形式
						csvIndex = str(v)
						csvKeyList = self.csvKeyCache.setdefault(csvIndex, [])
					else:
						csvKey = v
						if csvKey not in csvKeyList:
							csvKeyList.append(csvKey)
				# for i in range(len(linkData)//2):
				# 	csvIndex = linkData[2*i]
				# 	csvKey = linkData[2*i+1]
				# 	csvKeyList = self.csvKeyCache.setdefault(csvIndex, [])
				# 	if csvKey not in csvKeyList:
				# 		csvKeyList.append(csvKey)

		#行规则列表 暂不初始化收集CSV关键字列表
		csvRuleList = self.ruleDic.get("CSVRowRuleList",[])
		for ruleList in csvRuleList:
			for linkData in ruleList:
				csvKeyList = None
				parserCSV = False
				csvIndex = None
				csvKey = None
				for v in linkData:
					# Log("v:{0} parserCSV:{1} csvIndex:{2} csvKey:{3}".format(v,parserCSV,csvIndex,csvKey))
					if v == "CSVData":
						parserCSV = True
					elif v == "Bind":
						parserCSV = False
						csvIndex = None
						csvKey = None
					elif parserCSV:
						if csvIndex is None:
							#注意这里规则使用CSV文件名 不带后缀
							for index, csvFileName in self.csvNameCache.items():
								if csvFileName[:-4] == v:
									csvIndex = index
							# print("csvIndex:{0} csvName:{1}".format(csvIndex, v))
							csvKeyList = self.csvKeyCache.setdefault(csvIndex, [])
						elif csvKey is None:
							csvKey = v
							if csvKey not in csvKeyList:
								csvKeyList.append(csvKey)
		# Log("initCSVData csvKeyCache:{0}".format(self.csvKeyCache))

	def initCSVDataMatrix(self):
		self.csvDataMatrix = {}
		for csvIndex in self.csvKeyCache.keys():#仅读取所有规则需要的csv
			self.initCSVData(csvIndex)
		# Log("csvDataMatrix:{0}".format(self.csvDataMatrix))
		
	def initCSVData(self, csvIndex):
		csvName = self.getCSVNameByIndex(csvIndex)
		keyList = self.csvKeyCache.get(csvIndex)
		if csvName:
			csvData = readCSV(self.csvFolderPath, csvName, keyList)
			if csvData:
				self.csvDataMatrix[csvIndex] = csvData

	def getCSVNameByIndex(self, csvIndex, default=None):
		csvName = self.csvNameCache.get(csvIndex,default)
		if not csvName:
			printError("can't find csvIndex:{0} in CSVMap".format(csvIndex))
		return csvName

	def getCSVValueList(self, csvIndex, csvKey):
		csvData = self.csvDataMatrix.get(csvIndex)
		if csvData is not None:
			valueList = csvData.get(csvKey, [])
			return valueList
		else:
			printError("getCSVValueList can't find csvIndex:{0} in csvDataMatrix".format(csvIndex))
		return []

	def getCSVKeyRule(self, csvIndex, csvKey):
		csvKeyRuleDic = self.csvKeyRuleDicMatrix[csvIndex]
		if csvKeyRuleDic:
			return csvKeyRuleDic.get(csvKey, {})

	def getCSVFilterValueList(self, csvIndex, csvKey):
		valueList = self.getCSVValueList(csvIndex, csvKey)
		keyRule = self.getCSVKeyRule(csvIndex, csvKey)
		if keyRule:
			keyType = keyRule.get("type","String")
			if keyType == "Number":
				for i,value in enumerate(valueList):
					if not value.isdigit():
						printError("csvIndex:{0} in CSVKey:{1} valueList[{2}]:{3} is not convert Number".format(csvIndex, csvKey, i, value))
			elif keyType == "List":
				pass
		
		ignoreRange = keyRule.get("IgnoreRange",[])
		filterValueList = valueList
		if ignoreRange:
			print("ignoreRange",ignoreRange)
			print("valueList",valueList)
			for ignoreValue in ignoreRange:
				filterValueList = filter(lambda value: value != ignoreValue, filterValueList)
				filterValueList = list(filterValueList)
				# valueList.remove(ignoreValue)
			print("filterValueList",filterValueList)
		return filterValueList

	def showData(self):
		Log("csvNameCache:{0} \ncsvKeyCache:{1}".format(self.csvNameCache, self.csvKeyCache))
	# def checkAll(self):
	# 	for checkTree in self.ruleTreeList:
	# 		checkTree.run()

def main(*args,**kwargs):
	csvFolderPath = os.path.join(os.getcwd(),DefaultCSVFolder)
	checkRuleFilePath = os.path.join(os.getcwd(),DefaultCheckRuleName)
	rule = Rule(checkRuleFilePath,csvFolderPath)
	rule.initRule()

	csvRuleList = rule.ruleDic.get("CSVColRuleList", [])
	ruleTreeList = initTrees(rule,csvRuleList)
	checkAll(ruleTreeList)


	# csvRuleList = rule.ruleDic.get("FuncRuleList", [])
	# Log("FuncRuleList:{0}".format(csvRuleList))
	# for ruleList in csvRuleList:
	# 	headNode = initByRule(ruleList,None)
	# 	if headNode:
	# 		headNode.run()

	# csvRuleList = rule.ruleDic.get("CSVRowRuleList", [])
	# Log("CSVRowRuleList:{0}".format(csvRuleList))
	# for ruleList in csvRuleList:
	# 	headNode = initByRule(ruleList,None)
	# 	if headNode:
	# 		headNode.run()

	while True:
		command = input("run again with ang char or 空字符退出:")
		if command == "":
			break
		else:
			# rule.initRule()
			# rule.checkAll()
			pass
	pass

if __name__ == "__main__":
	main()
	# main(*args,**kwargs)