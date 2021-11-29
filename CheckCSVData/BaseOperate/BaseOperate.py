import os
import re

from BaseCore.Base import *
# from BaseCore.Base import Log
# from BaseCore.Base import BaseNode
# from BaseCore.Base import CalculateNode

class NewNode(BaseNode):
	def __init__(self, nodeName, instanceName):
		super(NewNode, self).__init__(nodeName, instanceName)
		NewNode.setArgsList(["Args","Rets","Handles"])#暂定操作参数为两个

	def getFieldByRule(self, fieldNameList, moveStep = 0):
		nodeName = fieldNameList[0]
		instanceName = fieldNameList[1]
		fieldName = fieldNameList[2]
		self.holdNode - globals()[nodeName].__init__(nodeName, instanceName)
		self.setMoveStep(moveStep+3)
		return fieldName

	def calculate(self):
		argsList = self.getArgNodeSlot("Args").getValue()
		self.holdNode.setArgsList(argsList)
		retsList = self.getArgNodeSlot("Rets").getValue()
		self.holdNode.setRetsList(retsList)
		handlesList = self.getArgNodeSlot("Handles").getValue()
		self.holdNode.setHandlesList(handlesList)
		self.holdNode.run()

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

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		nodeSlot = self.getArgNodeSlot("String")
		value = nodeSlot.getValue()
		print("PrintString +++++>>{0}".format(value))

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