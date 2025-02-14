import os
import re

from BaseCore.Base import *
# from BaseCore.Base import Log
# from BaseCore.Base import BaseNode
# from BaseCore.Base import CalculateNode

#主要用于 将函数名 申明为关键字 用于识别其所属类
class NewNode(BaseNode):
	def __init__(self, nodeName, instanceName):
		super(NewNode, self).__init__(nodeName, instanceName)
		NewNode.setArgsList(["Args","Rets","Handles"])#暂定操作参数为两个
		self.holdNode = None

	def getFieldByRule(self, fieldNameList, moveStep = 0):
		nodeName = None
		defaultFieldName = self.getDefaultFieldName()
		if len(fieldNameList) == 0:
			self.setMoveStep(moveStep)
			return defaultFieldName

		nodeName = fieldNameList[0]
		if nodeName == defaultFieldName:
			self.setMoveStep(moveStep+1)
			return defaultFieldName
		elif nodeName == "Link":
			self.setMoveStep(moveStep)
			return defaultFieldName

		cls = globals()[nodeName]
		if cls :
			instanceName = fieldNameList[1]
			fieldName = fieldNameList[2]
			Log("NewNode Init nodeName:{0} instanceName:{1} fieldName:{2}".format(nodeName, instanceName, fieldName))
			if self.holdNode is None:
				# self.holdNode = globals()[nodeName].__init__(nodeName, instanceName)
				# Log("NewNode cls:{0}".format(cls))
				# 函数类 这里仅声明函数  没有函数对象实例名
				# 创建对象为了将 函数名 申明为关键字 用于识别其所属类
				self.holdNode = cls(instanceName,None)
			self.setMoveStep(moveStep+3)
		else:
			fieldName = defaultFieldName		
		return fieldName

	def calculate(self):
		argsList = []
		retsList = []
		handlesList = []
		nodeSlot = self.getArgNodeSlot("Args")
		if nodeSlot:
			argsList = nodeSlot.getValue()
		self.holdNode.setArgsList(argsList)
		nodeSlot = self.getArgNodeSlot("Rets")
		if nodeSlot:
			retsList = nodeSlot.getValue()
		self.holdNode.setRetsList(retsList)
		nodeSlot = self.getArgNodeSlot("Handles")
		if nodeSlot:
			handlesList = nodeSlot.getValue()
		self.holdNode.setHandlesList(handlesList)
		# self.holdNode.run()
	
	# def run(self):
	# 	BaseNode.run(self)
	# 	if self.holdNode:
	# 		self.holdNode.run()

class Assign(CalculateNode):
	def __init__(self, nodeName, instanceName):
		super(Assign, self).__init__("Assign", instanceName, ["Variable","Value"],[],["Next"])

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		variableNode = self.getLocalArgPointer("Variable")
		valueNodeSlot = self.getArgNodeSlot("Value")
		value = valueNodeSlot.getValue()
		variableNode.setValue(value)

class Branch(CalculateNode):
	def __init__(self, nodeName, instanceName):
		super(Branch, self).__init__("Branch", instanceName,["Condition"],[],["True","False"])
	
	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		flag = self.getArgNodeSlot("Condition").getValue()
		handle = None
		if flag:
			handle = self.getHandleLinkNode("True")
		else:
			handle = self.getHandleLinkNode("False")

		if handle:
			handle.run()

class Sequeue(CalculateNode):
	def __init__(self, nodeName, instanceName, handlesList=[]):
		super(Sequeue, self).__init__("Sequeue", instanceName, [], [], handlesList)

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		for fieldName in self.getHandlesList():
			handle = self.getHandleLinkNode(fieldName)
			if handle:
				handle.run()

class PrintString(CalculateNode):
	def __init__(self, nodeName, instanceName):
		super(PrintString, self).__init__("PrintString", instanceName, ["String"],[],["Next"])
		self.appendList = None

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)
	
	def bindArgNodeSlot(self, fieldName, nodeSlot):
		if self.appendList is None:
			self.appendList = []
		if fieldName == "AppendString":
			self.appendList.append(nodeSlot)
		else:
			BaseNode.bindArgNodeSlot(self, fieldName, nodeSlot)

	def calculate(self):
		nodeSlot = self.getArgNodeSlot("String")
		value = nodeSlot.getValue()
		if self.appendList:
			for nodeSlot in self.appendList:
				value = value + nodeSlot.getValue()
		print("PrintString +++++++>>>>>{0}".format(value))

class ForArray(CalculateNode):
	def __init__(self, nodeName, instanceName):
		super(ForArray, self).__init__("ForArray", instanceName, ["List"],["Index","Value"],["Loop","Next"])

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		valueList = self.getLocalValue("List")
		for i,v in enumerate(valueList):
			self.bindReturnValue("Index", i)
			self.bindReturnValue("Value", v)
			loopHandle = self.getHandleLinkNode("Loop")
			if loopHandle:
				loopHandle.run()

def main(*args,**kwargs):
	pass

# if __name__ == "__main__":
	# main()
