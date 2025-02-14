import os
import re
import json
import csv

DefaultCSVFolder = "..\\..\\..\\Documents\\csv"#读取的CSV文件夹路径
DefaultCheckRuleName = "CheckRule.txt"

CSVFolderPath = None
CheckRuleFilePath = None

errorDic = []
errorState = None

def printError(errorStr):
	print(errorStr)
	errorDic.append(errorStr)

def getNodeLog(treeNode):
		csvName = treeNode.getCSVName()
		csvKeyList = treeNode.getCSVKeyList()
		return "<<{0} key:{1}>>".format(csvName,csvKeyList)

OpDic = {}# 操作字典
class OpNode:
	def __init__(self, checkType, opIndex, *args):
		self.checkType = checkType
		self.valueList = []
		self.argsList = args

	def getCheckType(self):
		return self.checkType

	def initValueList(self):
		if self.checkType == "Range":
			minValue = self.argsList[0]
			maxValue = self.argsList[1]
			for i in range(minValue,maxValue):
				self.valueList.append(i)
		elif self.checkType == "Filter":
			pass

	def getValueList(self): 
		if not self.valueList:
			self.initValueList()
		return self.valueList

	def getOutList(self):
		pass

class TreeNode:
	def __init__(self,csvName,csvKeyList,keyValueList,parent=None):
		self.csvName = csvName
		self.csvKeyList = csvKeyList
		self.keyValueList = keyValueList
		self.parent = parent
		self.childList = []

	def addChild(self,treeNode):
		treeNode.setParent(self)
		self.childList.append(treeNode)

	def setParent(self,treeNode):
		self.parent = treeNode

	def getCSVName(self):
		return self.csvName

	def getCSVKeyList(self):
		return self.csvKeyList

	def getValueList(self):
		return self.keyValueList

	def getChildList(self):
		return self.childList

#每条检测链都只有一个出口判断最后结果
  
class CheckTree:
	def __init__(self, treeHead):
		self.treeHead = treeHead

	# Message:{
	# 	valueList:List
	# 	valueType = ["Index","Value"]
	# }

	def run(self):
		inputValueList = self.treeHead.getValueList()
		checkType = "Value"
		childList = self.treeHead.getChildList()
		for childNode in childList:
			self.runCheck(inputValueList, self.treeHead, checkType, childNode)

	def checkData(self,leftValueList, leftTreeNode, checkType, rightTreeNode):
		resultValueList = []
		# leftValueList = leftTreeNode.getValueList()
		rightValueList = rightTreeNode.getValueList()
		if checkType == "Value":
			for value in leftValueList:
				findFlag = False
				if value in rightValueList:
					for v in rightValueList:
						if value == v:
							resultValueList.append(i)
							return
				else:
					printError("can't find {0} value:[{1}] in {2}".format(getNodeLog(leftTreeNode),value,getNodeLog(rightTreeNode)))
					return
		elif checkType == "Index":
			if len(leftValueList) != len(rightValueList):
				printError("len of ValueList is not equal! {0} with {1}".format(getNodeLog(leftTreeNode),getNodeLog(rightTreeNode)))
				return

			for index in leftValueList:
				resultValueList.append(rightValueList[index])

		return resultValueList

	def runCheck(self, inputValueList, leftTreeNode, checkType, rightTreeNode):
		outValueList = self.checkData(inputValueList, leftTreeNode, checkType, rightTreeNode)
		if not outValueList:
			return

		if checkType == "Index":
			checkType = "Value"
		elif checkType == "Value":
			checkType = "Index"
		
		childList = rightTreeNode.getChildList()
		for childNode in childList:
			self.runCheck(outValueList, rightTreeNode, checkType, childNode)

def readCSV(fileName, keyList):
	# filePath = os.path.join(os.getcwd(),DefaultCSVFolder,fileName)
	filePath = os.path.join(CSVFolderPath, fileName)
	if not os.path.exists(filePath):
		printError("csv path:{0} is not exists!".format(filePath))
		return
	with open(filePath,mode="r",encoding="utf-8-sig",errors="ignore") as f:
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
	def __init__(self):
		self.ruleDic = {}

		self.csvKeyCache = {}# csvIndex为key  查询csv的需要保存的key关键字
		self.csvNameCache = {}# csv文件名缓存(带后缀) csvIndex为key
		self.csvDataMatrix = {}# 数据总表   两层字典 key为csvIndex:csvKey  value为keyValueList
		self.ruleTreeList = []# 检查树 列表

		self.opDic = {}#

		self.errorList = []#错误信息

	def getCSVKeyValueList(self,csvIndex,csvKeyList):
		# print("getCSVKeyValueList csvIndex:{0} csvKeyList:{1}".format(csvIndex,csvKeyList))
		csvData = self.csvDataMatrix.get(csvIndex)
		keyValueList = []
		if csvData:
			value = ""
			for csvKey in csvKeyList:
				valueList = csvData.get(csvKey)
				if not valueList:
					printError("can't find csvKey:{0} in csvKeyList:{1} from csvIndex:{2} csv:{3}".format(csvKey,csvKeyList,csvIndex,csvName))
					return
				for index,value in enumerate(valueList):
					if len(keyValueList) == index:
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
		if not os.path.exists(CheckRuleFilePath):
			printError("CheckRulePath:{0} is not exists".format(CheckRuleFilePath))
			return

		with open(CheckRuleFilePath,mode="r",encoding="utf-8",errors="ignore") as f:
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
			printError("json loads rule File wrong:",e)
			printError("check rule File content in https://www.json.cn/")
			return

		self.initCSVList()
		self.initCSVDataMatrix()
		self.initTrees()

	def initCSVList(self):
		self.csvNameCache = {}
		csvMap = self.ruleDic.get("CSVMap", {})
		for csvIndex, csvName in csvMap.items():
			self.csvNameCache[csvIndex] = csvName+".csv"

		self.csvKeyCache = {}
		csvRuleList = self.ruleDic.get("CSVRuleList", [])
		for treeData in csvRuleList:
			for linkData in treeData:
				csvKeyList = None
				for v in linkData:
					if v.isdigit():
						csvIndex = v#注意这里索引采用数字的字符串形式
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
		
	def initCSVDataMatrix(self):
		self.csvDataMatrix = {}
		for csvIndex in self.csvKeyCache.keys():#仅读取所有规则需要的csv
			self.initCSVData(csvIndex)
		
	def initCSVData(self, csvIndex):
		csvName = self.getCSVNameByIndex(csvIndex)
		keyList = self.csvKeyCache.get(csvIndex)
		if csvName:
			csvData = readCSV(csvName, keyList)
			if csvData:
				self.csvDataMatrix[csvIndex] = csvData

	def initCheckTree(self, treeData):
		treeHead = None

		nodeMap = {}
		treeNodeList = []
		for linkData in treeData:
			lastNode = None
			csvIndex = None
			csvKeyList = None
			for v in linkData:
				if v.isdigit():
					csvIndex = v#注意这里索引采用数字的字符串形式
					csvKeyList = []
					# 记录节点数据
					treeNodeList.append(csvIndex)
					treeNodeList.append(csvKeyList)
				else:
					csvKeyList.append(v)

		# print("treeNodeList",treeNodeList)
		for i in range(len(treeNodeList)//2):
			csvIndex = treeNodeList[2*i]
			csvKeyList = treeNodeList[2*i+1]
		
			nodeKey = "{0}".format(csvIndex)
			for key in csvKeyList:
				nodeKey = nodeKey + "_" + key
			node = nodeMap.get(nodeKey)
			if not node:
				keyValueList = self.getCSVKeyValueList(csvIndex, csvKeyList)
				if not keyValueList:
					return
				csvName = self.getCSVNameByIndex(csvIndex)
				if csvName:
					node = TreeNode(csvName, csvKeyList, keyValueList)
					if treeHead is None:
						treeHead = node

			if lastNode is None:
				lastNode = node
			else:
				lastNode.addChild(node)#设置数据间关系
				lastNode = node

		return treeHead

	def initTrees(self):
		self.ruleTreeList = []
		csvRuleList = self.ruleDic.get("CSVRuleList", [])
		# print("csvRuleList", csvRuleList)
		for treeData in csvRuleList:
			# print("treeData",treeData)
			treeHead = self.initCheckTree(treeData)
			if treeHead:
				self.ruleTreeList.append(CheckTree(treeHead))

	def showData(self):		
		print("ruleDic",self.ruleDic)
		print("csvKeyCache",self.csvKeyCache)
		print("csvNameCache",self.csvNameCache)
		print("csvDataMatrix",self.csvDataMatrix)
		print("ruleTreeList",self.ruleTreeList)
		pass

	def getCSVNameByIndex(self, csvIndex, default=None):
		csvName = self.csvNameCache.get(csvIndex,default)
		if not csvName:
			printError("can't find csvIndex:{0} in CSVMap".format(csvIndex))
		return csvName

	def checkAll(self):
		for checkTree in self.ruleTreeList:
			checkTree.run()

def main(*args,**kwargs):
	global CSVFolderPath,CheckRuleFilePath
	CSVFolderPath = os.path.join(os.getcwd(),DefaultCSVFolder)
	CheckRuleFilePath = os.path.join(os.getcwd(),DefaultCheckRuleName)
	rule = Rule()
	rule.initRule()
	rule.checkAll()
	# rule.showData()
	while True:
		command = input("run again with ang char or 空字符退出:")
		if command == "":
			break
		else:
			rule.initRule()
			rule.checkAll()
			# rule.showData()
	pass

if __name__ == "__main__":
	main()
	# main(*args,**kwargs)