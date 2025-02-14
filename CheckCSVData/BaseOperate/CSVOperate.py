import os
import re
import csv

from BaseCore.Base import *
# from BaseCore.Base import Log
# from BaseCore.Base import BaseNode
# from BaseCore.Base import ValueNode
# from BaseCore.Base import CalculateNode

class CSVData(ValueNode):
	def readCSV(self, csvName):
		DefaultCSVFolder = "CSVData"#"..\\NZTrunk\\Documents\\csv"
		filePath = os.path.join(os.getcwd(), DefaultCSVFolder, csvName+".csv")
		with open(filePath, mode="r", encoding="utf-8-sig",errors="ignore") as f:
			lineIndex = 0
			keyIndexDic = {}
			dataMatrix = {}
			f_csv = csv.reader(f)
			for rowDataList in f_csv:
				lineIndex = lineIndex + 1
				if lineIndex == 1:
					for i, key in enumerate(rowDataList):
						keyIndexDic[i] = key#后续值替换为dataMatrix.get(key)
					for i, key in keyIndexDic.items():
						keyIndexDic[i] = dataMatrix.setdefault(key, [])
					continue
				if lineIndex != 2:#第二行默认为描述
					for i, value in enumerate(rowDataList):
						dataList = keyIndexDic.get(i)#空表和None的判断结果一样
						if dataList is not None:
							dataList.append(value)
			return dataMatrix

	def __init__(self, nodeName, instanceName):
		Log("CSVData nodeName:{0} instanceName:{1}".format(nodeName, instanceName))
		self.dataMatrix = self.readCSV(instanceName)
		retsList = []
		for key in self.dataMatrix.keys():
			retsList.append(key)
		self.setArgsList([])
		self.setRetsList(retsList)
		self.setHandlesList([])
		super(ValueNode, self).__init__(nodeName, instanceName)
		self.initRetsNodeSlot()

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return 1

	def getValue(self, fieldName):
		# Log("CSVData fieldName:{0} valueList:{1}".format(fieldName, self.dataMatrix.get(fieldName)))
		return self.dataMatrix.get(fieldName)

class GetListIndexByValue(CalculateNode):
	def __init__(self, nodeName, instanceName):
		super(GetListIndexByValue, self).__init__("GetListIndexByValue", instanceName, ["List","Value"],["Result"],["Next"])

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		nodeSlot = self.getArgNodeSlot("List")
		valueList = nodeSlot.getValue()
		nodeSlot = self.getArgNodeSlot("Value")
		value = nodeSlot.getValue()
		# Log("GetListIndexByValue value:{0} list:{1}".format(value, valueList[:10]))
		if value in valueList:
			index = valueList.index(value)
			self.bindReturnValue("Result",index)
		else:
			self.bindReturnValue("Result",None)

class GetListValueByIndex(CalculateNode):
	def __init__(self, nodeName, instanceName):
		super(GetListValueByIndex, self).__init__("GetListValueByIndex", instanceName, ["List","Index"],["Result"],["Next"])

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return BaseNode.getInsMoveStepByRule(keyWord)

	def calculate(self):
		nodeSlot = self.getArgNodeSlot("List")
		valueList = nodeSlot.getValue()
		nodeSlot = self.getArgNodeSlot("Index")
		index = nodeSlot.getValue()
		# Log("GetListValueByIndex index:{0} list:{1}".format(index, valueList[:10]))
		if index < len(valueList):
			value = valueList[index]
			self.bindReturnValue("Result",value)
		else:
			self.bindReturnValue("Result",None)

def main(*args,**kwargs):
	pass

# if __name__ == "__main__":
# 	main()
