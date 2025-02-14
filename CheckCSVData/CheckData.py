#!usr/bin/python
import os
import sys
import re

class TreeNode:
	def __init__(self, csvName, csvKey, keyValueList)
		self.csvName = csvName
		self.csvKey = csvKey
		self.keyValueList = keyValueList
		self.childList = []
		self.parent = None

	def setParent(self, treeNode):
		self.parent = treeNode

	def addChild(self, treeNode):
		treeNode.setParent(self)
		self.childList.append(treeNode)

	def getChildList(self):
		return self.childList

	def getValueList(self):
		return self.keyValueList

	def getCSVName(self):
		return self.csvName

	def getCSVKey(self):
		return self.csvKey

def Op(input,node):  
	pass


def CheckTree:
	def __init__(self, treeHead):
		self.treeHead = treeHead

	# resultList 是上一次节点运算的结果
	def checkData(self, resultList, leftTreeNode, checkType, rightTreeNode):
		resultList = []
		if checkType == "Index":
			indexList = leftTreeNode.getValueList()
			valueList = rightTreeNode.getValueList()
			if len(indexList) != len(valueList):
				print("check dataList is not same length")
			else:
				for index in indexList:
					resultList.append(valueList[index])
		elif checkType == "Value":
			valueList = leftTreeNode.getValueList()
			compList = rightTreeNode.getValueList()
			for value in valueList:
				if value in compList:
					index = compList.index(value)
					resultList.append(index)
				else:
					print("check data not in valueList!")
		else:
			print("error checkType:".format(checkType))

		if resultList:
			if checkType == "Index":
				checkType = "Value"
			elif checkType == "Value":
				checkType = "Index"
			childList = self.rightTreeNode.getChildList()
			for childNode in childList:
				checkData(resultList, self.rightTreeNode, checkType, childNode)

	def runCheck(self):
		resultList = self.treeHead.getValueList()
		childList = self.treeHead.getChildList()
		for childNode in childList:
			self.checkData(resultList, self.treeHead, "Value", childNode)

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