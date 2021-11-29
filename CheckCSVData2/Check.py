import os
import re
import json
import csv

errorDic = []
errorState = None

def printError(errorStr):
	print(errorStr)
	errorDic.append(errorStr)

def getNodeLog(treeNode):
		csvName = treeNode.getCSVName()
		csvKeyList = treeNode.getCSVKeyList()
		return "<<{0} key:{1}>>".format(csvName,csvKeyList)

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
					for i,v in enumerate(rightValueList):
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

def initCheckTree(ruleObj, treeData):
	treeHead = None

	nodeMap = {}
	treeNodeList = []
	for linkData in treeData:
		lastNode = None
		csvIndex = None
		csvKeyList = None
		for v in linkData:
			if type(v) == int:
				csvIndex = str(v)
			# if v.isdigit():
			# 	csvIndex = v#注意这里索引采用数字的字符串形式
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
			keyValueList = ruleObj.getCSVKeyValueList(csvIndex, csvKeyList)
			if not keyValueList:
				return
			csvName = ruleObj.getCSVNameByIndex(csvIndex)
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

# csvRuleList = self.ruleDic.get("CSVRuleList", [])
def initTrees(ruleObj,csvRuleList):
	ruleTreeList = []
	for treeData in csvRuleList:
		# print("treeData",treeData)
		treeHead = initCheckTree(ruleObj,treeData)
		if treeHead:
			ruleTreeList.append(CheckTree(treeHead))
	return ruleTreeList

def checkAll(ruleTreeList):
	for checkTree in ruleTreeList:
		checkTree.run()

def main(*args,**kwargs):
	DefaultCSVFolder = "..\\NZTrunk\\Documents\\csv"#读取的CSV文件夹路径
	DefaultCheckRuleName = "CheckRule.json"
	csvFolderPath = os.path.join(os.getcwd(),DefaultCSVFolder)
	checkRuleFilePath = os.path.join(os.getcwd(),DefaultCheckRuleName)
	
	rule = Rule(checkRuleFilePath,csvFolderPath)
	rule.initRule()

	# Log("ruleDic:{0}".format(rule.ruleDic))
	csvRuleList = rule.ruleDic.get("CSVColRuleList", [])
	Log("CSVColRuleList:{0}".format(csvRuleList))
	ruleTreeList = initTrees(rule,csvRuleList)
	Log("ruleTreeList:{0}".format(ruleTreeList))
	checkAll(ruleTreeList)

if __name__ == "__main__":
	from Run import *
	main()
	# main(*args,**kwargs)