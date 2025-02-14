#!usr/bin/python
import os
import sys
import re

'''
For:["initSequeue","conditionSequeue"，"deltaSequeue","loopSequeue"]
	initSequeue,conditionSequeue,Branch:["temp"]
	Branch:["temp"]:True,loopSequeue,deltaSequeue,conditionSequeue
	//Branch["temp"]:False
'''
_LocalValueDic = {}# 局部变量字典
_GlobalValueDic = {}# 全局变量字典

class BaseNode:
	instanceIndex = 0
	instanceDic = {}
	def __init__(self, nodeName, instanceName=None)
		self.nodeName = nodeName#对应节点的类型
		self.instanceName = instanceName



		self.argsNum = 0#最大参数个数
		self.argsDic = {}
		self.argDefaultDic = {}
		self.moveStep = 0#前进步数 对应消耗的实参个数

	def getArgsNum(self):
		return self.argsNum

	def getMoveStep(self):
		return self.moveStep

class NodeLink:
	"""链接每个逻辑节点"""
	def __init__(self, arg):
		# super(NodeLink, self).__init__()
		self.arg = arg

class OperateNode:
	def __init__(self):
		self.operateType = None# 枚举操作类型 
		self.leftValue = None# 左操作值
		self.rightValue = None# 右操作值
    
		# 操作节点需要反向寻找入口的逻辑链头
		pass

	def getValue(self):
		if self.operateType == "Add":
			l = self.leftValue.getValue()
		elif self.operateType == "Not":
			return not self.leftValue.getValue()
		else
			return self.leftValue.getValue()

class ValueNode:
	def __init__(self, valueName, valueType, value):
		'''valueType 局部变量 全局变量 字面量 表达式'''
		self.valueName = valueName
		self.valueType = valueType
		self.value = value# 表达式类型时 value为OperateNode

	def getValue():
		if self.valueType == "Local":
			return _GlobalValueDic.get(self.valueName)
		elif self.valueType == "Global":
			return _GlobalValueDic.get(self.valueName)
		elif self.valueType == "Expression":
			return self.value.getValue()

class CalculateNode:
	"""计算节点"""
	def __init__(self):
		# super(CalculateNode, self).__init__()
		self.valueName = None# 实例名 用于全局查找

		self.argNameList = []# 参数变量名列表
		self.argValueNodeDic = {}# 参数节点字典

		# 代码中一般返回值没有名字 蓝图中的返回值具有名字
		self.returnValueNameList = []# 返回值变量名列表
		self.returnValueNodeDic = {}# 返回值节点字典
		self.returnValueDic = {}# 返回值字典

		# 分支具备两个句柄 对应条件真假分支
		# Sequeue序列具备多个句柄 顺序执行各个句柄
		self.handleNameList = []# 句柄名字列表
		self.handleSlotDic = {}# 句柄对应逻辑链字典

		self.localValueDic = {}# 局部变量字典

		self.nextHandleSlot = None# 下一个逻辑链 
	def getArgValue(self, argName):
		return self.argValueNodeDic.get(argName, None)

	def getReturnValue(self, returnValueName):
		return self.returnValueNodeDic.get(returnValueName, None)

	def getHandleSlot(self, handleName):
		return self.handleSlotDic.get(handleName, None)
		
	def bindArgValue(self, argName, value):
		self.argValueNodeDic[argName] = value

	def bindReturnValue(self, returnValueName, value):
		self.returnValueNodeDic[returnValueName] = value

	def bindHandle(self, handleName, value):
		self.handleSlotDic[handleName] = value

	def initArg(self):
		for argName, valueNode in self.argValueNodeDic.items():
			self.localValueDic[argName] = valueNode.getValue()

	def initReturn(self):
		for returnValueName, returnValueNode in self.returnValueNodeDic.items():
			self.returnValueDic[returnValueName] = returnValueNode.getValue()

	def run(self):


def initLinkNode(self, ruleList):
	# 根据配置初始化事务逻辑链
	# ["CSVData","6","UnlockCondition","Equal","Left"]
	# ["String","","Equal","Right"]
	# ["Branch","True","GetColList","GetColData","Parm1","CSVData","6","ItemId"]
	# ["Branch","Result"]
	# 
	# CSVData,6,UnlockCondition bind ForArray
	# ForArray loop Link Branch
	# ForArray v Equal Left
	# String "" Equal Right
	# Equal Result Branch condition
	# Branch True Link GetColList
	# ForArray i GetColList, index
	# CSVData 6 GetColList csv
	# GetColList Link GetColData
	# 
	# 每个节点定义了参数个数 可有默认参数值
	HeadNode = None
	for rule in ruleList:
		index = 0
		maxIndex = lenght(rule)
		while index < maxIndex:
			ruleKey = rule[index]
			node = InitNodeByKey(ruleKey, *args)
			argsNum = node.getArgsNum()
			args = []
			for j in range(0,argsNum):
				args.append(rule[index+j+1])
			moveStep = node.getMoveStep()# 返回前进步数

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