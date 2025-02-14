import os
import re
import csv
# from ..main import GetNodeInsByRule
	# 规则定义
	# NodeIns = NodeName、InstanceName 可省略InstanceName
	# NodeSlot = NodeIns、Field 返回值
	# NodeIns、Field代表参数、句柄
	# NodeIns、Field、[Bind|Link]、NodeIns
	# A节点返回值绑定B节点参数
	# A节点句柄绑定B节点
LogTag = 0
LogLimitList = [
	# "Equal",
	# "Print",
	# "Equal",
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


# 遗留问题
# 多参数初始化问题(子类重复定义argsNum来获取规则关键字+自定义函数进行初始化)

# 多参数初始化就是  辨别Node以及获取对应的关键字
#  Bink等特殊关键字怎么排除？？ 包含特殊关键字的结点(其不可省略Field)

# 子类的初始化参数不同 如何统一？？？？
# 标识每一个结点的必要参数信息  必然在规则中不会缺失(准确指明一个结点必然具备必要参数)

# 绑定结点的返回字段 用于初始化其它结点的参数
# 在函数还未运行时,就可以绑定返回字段
class NodeSlot:#用于获取或绑定结点返回值
	def __init__(self, node, field = "Result"):
		self.node = node
		self.field = field

	def getValue(self):
		# print("getNodeSlotValue node:{0} value:{1}".format(self.node,self.node.getValue(self.field)))
		return self.node.getValue(self.field)

class BaseNode:
	SubNodeInsDic = {}# 存储各子类实例化对象字典  以NodeName为key

	# 解析规则使用
	subNodeClassDic = {}# 记录规则的关键字段对应类名
	localFuncValueDicStack = []#函数的局部变量字典栈

	# 子类的初始化参数必须保持一致 nodeName、instanceName就可以标识唯一结点了 
	# 规则中两字段标识结点也简洁
	def __init__(self,nodeName,instanceName):
		self.nodeName = nodeName#结点名字对应类名 不是实例名  用于规则的关键字判断
		self.instanceName = instanceName# 实例化对象序号
		self.initNodeInstance()

		# 参数和返回值 通过绑定NodeSlot对象
		# NodeSlot对象是为了绑定结点间数据关系(未能取值的时候先绑定关系)
		self.argNodeSlotDic = {}#指向一个NodeSlot对象
		self.returnNodeSlotDic = {}#初始化维持一个NodeSlot对象
		self.retValueDic = {}#记录返回值
		self.handleLinkNodeDic = {}#指向一个实例结点

		self.localValueDic = {}#局部变量字典  存放实参及内部局部变量
		#函数内采用封闭作用域  没有全局变量节点的概念

		self.moveStep = 0#对应的前进步数 对应规则读取数据的实际消耗  为实现默认参数

	def __repr__(self):
		return "nodeName:{0} instanceName:{1}".format(self.nodeName,self.instanceName)
		# return "\nnodeName:{0} instanceName:{1} \n----> argsList:{2} \n----> retsList:{3} \n----> handlesList:{4}".format(
		# 	self.nodeName,self.instanceName,
		# 	self.getArgsList(),self.getRetsList(),self.getHandlesList(),
		# )

	# 子类实例化时记录实例对象
	def initNodeInstance(self):
		# print("initNodeInstance", self.nodeName, self.instanceName)
		insDic = BaseNode.SubNodeInsDic.setdefault(self.nodeName, {})
		insDic[self.instanceName] = self

	@staticmethod
	def getNodeInstance(nodeName, instanceName):
		insDic = BaseNode.SubNodeInsDic.get(nodeName, {})
		return insDic.get(instanceName, None)

	# @classmethod
	# def getInstanceName(cls):
	# 	return BaseNode.SubNodeInsIndex.setdefault(cls.nodeName, 0)

	@staticmethod
	def pushFuncLocalDic(funcNode):
		BaseNode.localFuncValueDicStack.append(funcNode.localValueDic)

	@staticmethod
	def popFuncLocalDic():
		return BaseNode.localFuncValueDicStack.pop()

	@staticmethod
	def getFuncLocalDic():
		return {}
		# return BaseNode.localFuncValueDicStack[-1]

	@classmethod
	def setArgsList(cls, argsList):
		if type(argsList) is list:
			cls.argsList = argsList
		else:
			cls.argsList = []

	@classmethod
	def getArgsList(cls):
		if hasattr(cls, "argsList") is False:
			cls.argsList = []
		return cls.argsList

	def getArgNodeSlot(self, fieldName):
		if fieldName in self.argsList:
			return self.argNodeSlotDic.get(fieldName)

	def getArgValue(self, fieldName):
		if fieldName in self.argsList:
			nodeSlot = self.argNodeSlotDic.get(fieldName)
			if nodeSlot:
				return nodeSlot.getValue()

	def bindArgNodeSlot(self, fieldName, nodeSlot):
		self.argNodeSlotDic[fieldName] = nodeSlot

	def getLocalValue(self, fieldName):
		return self.localValueDic.get(fieldName)

	def getLocalArgPointer(self, fieldName):
		nodeSlot = self.getArgNodeSlot(fieldName)
		if nodeSlot:
			return nodeSlot.node

	@classmethod
	def setRetsList(cls, retsList):
		if type(retsList) is list:
			cls.retsList = retsList
		else:
			cls.retsList = []

	@classmethod
	def getRetsList(cls):
		if hasattr(cls, "retsList") is False:
			cls.retsList = []
		return cls.retsList

	def initRetsNodeSlot(self):
		for fieldName in self.retsList:
			self.returnNodeSlotDic[fieldName] = NodeSlot(self, fieldName)

	def getRetNodeSlot(self, fieldName):
		if fieldName in self.retsList:
			return self.returnNodeSlotDic.get(fieldName)

	# 返回值 在函数结束时保存在函数实例中 随调用而改变
	# 需要使用该次调用的返回值 只需要在下次调用前取出数据并保存
	def getReturnValue(self, fieldName):
		# print("getReturnValue nodeName:{0} fieldName:{1} value:{2}".format(self.nodeName, fieldName, self.retValueDic.get(fieldName, None)))
		return self.retValueDic.get(fieldName, None)

	# 暂时没有好的调用逻辑及顺序
	def bindReturnValue(self, fieldName, value):
		# print("bindReturnValue nodeName:{0} fieldName:{1} value:{2}".format(self.nodeName, fieldName, value))
		self.retValueDic[fieldName] = value

	@classmethod
	def setHandlesList(cls, handlesList):
		if type(handlesList) is list:
			cls.handlesList = handlesList
		else:
			cls.handlesList = []

	@classmethod
	def getHandlesList(cls):
		if hasattr(cls, "handlesList") is False:
			cls.handlesList = []
		return cls.handlesList

	def getHandleLinkNode(self, fieldName):
		if fieldName in self.handlesList:
			return self.handleLinkNodeDic.get(fieldName)

	def linkNodeFiled(self, fieldName, nextNode):
		self.handleLinkNodeDic[fieldName] = nextNode

	# -- 在getInsMoveStepByRule及getFieldByRule中分别定义消耗的次数
	def setMoveStep(self, moveStep):
		self.moveStep = moveStep

	def getMoveStep(self):
		return self.moveStep

	# 各个子类重定义
	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		moveStep = 0
		if type(keyWord) is int:#默认实例名必须为数字 为了区分
			moveStep = 1
		return moveStep

	# 各个子类重定义
	# 根据各子类的实例名初始化逻辑  获取字段进行初始化
	# 根据实际使用逻辑修改该对象的数据
	def getFieldByRule(self, fieldNameList, moveStep = 0):
		if fieldNameList is None:
			return self.getDefaultFieldName()
		fieldName = fieldNameList[0]
		argsList = self.getArgsList()
		retsList = self.getRetsList()
		handlesList = self.getHandlesList()
		if (fieldName in argsList) or (fieldName in retsList) or (fieldName in handlesList):
			self.setMoveStep(moveStep+1)
			return fieldName
		else:
			self.setMoveStep(moveStep)
			return self.getDefaultFieldName()

	def getDefaultFieldName(self):
		return "Result"

	def initLocalArgs(self):
		for argName in self.getArgsList():
			# print("nodeName:{0} instanceName:{1} initLocalArgs argName:{2}".format(self.nodeName, self.instanceName, argName))
			argNodeSlot = self.getArgNodeSlot(argName)
			if argNodeSlot:
				self.localValueDic[argName] = argNodeSlot.getValue()
			else:
				print("argName is not bind NodeSlot")

	# 各个子类重定义
	# 主体逻辑及绑定存放返回值
	def calculate(self):
		# self.getLocalValue(fieldName)#获取实参
		# self.bindReturnValue(fieldName, value)#绑定返回值
		pass

	# 定义结点后续
	def runNext(self):
		nextNode = self.getHandleLinkNode("Next")
		if nextNode:
			nextNode.run()

	def run(self):
		self.initLocalArgs()#实参初始化
		self.calculate()#运行主体逻辑及绑定存放返回值
		self.runNext()

	def WaitBind(self, fieldNameList, node):
		self.fieldNameList = fieldNameList
		self.waitNode = node

	def SetBind(self, fieldName):
		if fieldName in self.fieldNameList:
			self.fieldNameList.remove(fieldName)
			if not self.fieldNameList:
				self.waitNode.run()

	@staticmethod
	def RunNextNode():
		if BaseNode.nextNode:
			BaseNode.nextNode.run()

	@staticmethod
	def setRunNextNode(nextNode):
		BaseNode.nextNode = nextNode


class ValueNode(BaseNode):
	'''局部变量 全局变量 表达式'''
	def __init__(self, valueType, valueName):
		print("ValueNode valueType:{0} valueName:{1}".format(valueType, valueName))
		# BaseNode.subNodeClassDic.setdefault(valueType, ValueNode)
		super(ValueNode, self).__init__(valueType, valueName)#结点类型名
		ValueNode.setArgsList([])
		ValueNode.setRetsList(["Result"])
		ValueNode.setHandlesList([])
		self.initRetsNodeSlot()

	def setValue(self, value):
		fieldName = self.getDefaultFieldName()
		self.bindReturnValue(fieldName, value)

	# 各个子类重定义
	def getValue(self, fieldName=None):
		if fieldName is None:
			fieldName = self.getDefaultFieldName()
		elif fieldName != "Result":
			print("ValueNode getValue(fieldName={0}) is error! fieldName need be Result".format(fieldName))
		return self.getReturnValue(fieldName)

	# # 数值结点 获取返回值结果 是取值时运算逻辑
	# def calculate(self):
	# 	self.setValue(None)#绑定返回值

# 表达式
class OperateNode(ValueNode):
	'''操作节点  其值在取值时进行计算'''
	'''蓝图取值之前 对该值的计算不像程序语言那样 在定义处运行  而是在取值时再计算'''
	# argsNum = 2#操作结点操作数一致   instanceId、Field
	def __init__(self, operateType,instanceId=None):
		BaseNode.subNodeClassDic.setdefault(operateType, OperateNode)
		# 直接调用ValueNode的父类BaseNode  不调用ValueNode的__init__方法
		super(ValueNode, self).__init__(operateType,instanceId)#结点类型名
		OperateNode.setArgsList(["Left","Right"])#暂定操作参数为两个
		OperateNode.setRetsList(["Result"])
		OperateNode.setHandlesList([])
		self.initRetsNodeSlot()
		self.operateType = operateType# 枚举操作类型

		# 各个子类重定义
	def getValue(self,fieldName=None):
		if fieldName is None:
			fieldName = self.getDefaultFieldName()
		elif fieldName != "Result":
			print("Error")
		self.run()#取值时重新运算逻辑
		return self.getReturnValue(fieldName)

	def calculate(self):
		# print("OperateNode",self)
		if self.operateType == "Add":
			l = self.getArgValue("Left")
			r = self.getArgValue("Right")
			self.setValue(l + r)
		elif self.operateType == "Not":
			l = self.getArgValue("Left")
			self.setValue(not l)
		elif self.operateType == "And":
			l = self.getArgValue("Left")
			r = self.getArgValue("Right")
			self.setValue(l and r)
		elif self.operateType == "Equal":
			l = self.getArgValue("Left")
			r = self.getArgValue("Right")
			# Log("Equal instanceName:{2} l:{0} r:{1}".format(l,r,self.instanceName))
			self.setValue(l == r)
		elif self.operateType == "Less":
			l = self.getArgValue("Left")
			r = self.getArgValue("Right")
			self.setValue(l < r)

class CalculateNode(BaseNode):
	def __init__(self, nodeName, valueName, argsList=[],retsList=[],handlesList=[]):
		# argsList, retsList, handlesList三个参数由规则定义
		# print("CalculateNode nodeName:{0} valueName:{1}".format(nodeName, valueName))
		# if nodeName is None:#动态参数节点
		# print("nodeName is None")
		super(CalculateNode, self).__init__(nodeName,valueName)#结点类型名
		self.setArgsList(argsList)
		self.setRetsList(retsList)
		self.setHandlesList(handlesList)
		self.initRetsNodeSlot()
		# else:#特定类(固定参数)的节点
		# 	print("nodeName is not None:{0}".format(nodeName))
		# 	super(CalculateNode, self).__init__(nodeName,valueName)#结点类型名
		# 	print("globals()[nodeName={0}]:{1}".format(nodeName, globals()[nodeName]))
		# 	globals()[nodeName].setArgsList(argsList)
		# 	globals()[nodeName].setRetsList(retsList)
		# 	globals()[nodeName].setHandlesList(handlesList)
		# pass

	#重载设置参数、返回值、句柄等列表  将数据下放到实例对象
	def setArgsList(self, argsList):
		if type(argsList) is list:
			self.argsList = argsList
		else:
			self.argsList = []

	def getArgsList(self):
		if hasattr(self, "argsList") is False:
			self.argsList = []
		return self.argsList

	def setRetsList(self, retsList):
		if type(retsList) is list:
			self.retsList = retsList
		else:
			self.retsList = []

	def getRetsList(self):
		if hasattr(self, "retsList") is False:
			self.retsList = []
		return self.retsList

	def setHandlesList(self, handlesList):
		if type(handlesList) is list:
			self.handlesList = handlesList
		else:
			self.handlesList = []

	def getHandlesList(self):
		if hasattr(self, "handlesList") is False:
			self.handlesList = []
		return self.handlesList

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return 1

	def getValue(self, fieldName):
		return self.getReturnValue(fieldName)

# 复合节点  对应函数
# 局部变量仅在函数内部有意义
# 函数进入和退出 设置局部变量栈序号
class Composite(CalculateNode):
	def __init__(self, valueName, instanceName, argsList=[],retsList=[],handlesList=[]):
		BaseNode.subNodeClassDic.setdefault(valueName, self)
		print("Composite valueName:{0} instanceName:{1}".format(valueName, instanceName))
		super(Composite, self).__init__(valueName,instanceName,argsList,retsList,handlesList)

		self.startNode = CalculateNode("CalculateNode","startNode",["Test"],argsList,["Next"])
		self.endNode = CalculateNode("CalculateNode","endNode",retsList,[],handlesList)
		# print("startNode",self.startNode)
		# print("endNode",self.endNode)

	@staticmethod
	def LinkStartNode(nodeName, instanceName=None):
		rule = ["CalculateNode","startNode","Next","Link"]
		rule.append(nodeName)
		if instanceName:
			rule.append(instanceName)
		return rule

	@staticmethod
	def LinkEndNode(nodeName, instanceName=None, fieldName=None):
		rule = []
		rule.append(nodeName)
		if instanceName:
			rule.append(instanceName)
		if fieldName:
			rule.append(fieldName)
		rule.extend(["Link","CalculateNode","endNode"])
		return rule

	def calculate(self):
		for fieldName in self.getArgsList():#函数实参初始化
			self.startNode.bindReturnValue(fieldName, self.getLocalValue(fieldName))
		for fieldName in self.getHandlesList():#函数句柄初始化
			self.endNode.linkNodeFiled(fieldName, self.getHandleLinkNode(fieldName))
		self.startNode.run()#运行函数主体逻辑
		for fieldName in self.getRetsList():
			self.bindRetValueNode(fieldName, self.endNode.getLocalValue(fieldName))

# 局部变量仅在函数内部有意义
class LocalValue(ValueNode):
	def __init__(self, valueType, valueName):
		# print("LocalValue:{0} init".format(valueName))
		if valueType != "LocalValue":
			print("LocalValue(valueType={0},value={1}), valueType ~= 'String'".format(valueType,value))
			valueType = "LocalValue"
		super(LocalValue, self).__init__(valueType,valueName)#结点类型名

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return 1

	def setValue(self, value):
		# localValueDic = BaseNode.getFuncLocalDic()
		# if localValueDic.get(self.instanceName) is not None:
		# 	print("LocalValue valueName:{0} is exsit!!! valueName may be argName")
		# localValueDic.setdefault(self.instanceName, value)
		self.bindReturnValue("Result", value)

# 字面量 名字为其值
class String(ValueNode):
	def __init__(self, valueType, value):
		if valueType != "String":
			print("String(valueType={0},value={1}), valueType ~= 'String'".format(valueType,value))
			valueType = "String"
		super(String, self).__init__(valueType, value)

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return 1

	def getFieldByRule(self, fieldNameList):
		self.bindReturnValue("Result", str(self.instanceName))
		return ValueNode.getFieldByRule(self, fieldNameList)

	def setValue(self, value):
		print("String is literal, can't setValue value:{0}".format(value))

class Int(ValueNode):
	def __init__(self, valueType, value):
		# print("Int init:{0}".format(value))
		if valueType != "Int":
			print("Int(valueType={0},value={1}), valueType ~= 'Int'".format(valueType,value))
			valueType = "Int"
		super(Int, self).__init__(valueType, value)

	# 默认实例名就是数字 该函数可省略重载
	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		return 1

	def getFieldByRule(self, fieldNameList):
		self.bindReturnValue("Result", int(self.instanceName))
		return ValueNode.getFieldByRule(self, fieldNameList)

	def setValue(self, value):
		print("Int is literal, can't setValue value:{0}".format(value))

class List(ValueNode):
	def __init__(self, valueType, value):
		if valueType != "List":
			print("List(valueType={0},value={1}), valueType ~= 'List'".format(valueType,value))
			valueType = "List"
		super(List, self).__init__(valueType, value)
		self.bindReturnValue("Result", [])

	@classmethod
	def getInsMoveStepByRule(cls, keyWord):
		moveStep = 0
		if type(keyWord) is int:#默认实例名必须为数字 为了区分
			moveStep = 1
		return moveStep

	def getFieldByRule(self, fieldNameList):
		num = self.instanceName
		dataList =  []
		for i in range(0,num):
			dataList.append(fieldNameList[i])
		self.bindReturnValue("Result", dataList)
		return ValueNode.getFieldByRule(self, fieldNameList[num:], num)

	def setValue(self, value):
		print("List is literal, can't setValue value:{0}".format(value))

def main(*args,**kwargs):
	pass

# if __name__ == "__main__":
# 	main()