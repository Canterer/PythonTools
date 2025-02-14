import os
from BaseCore.Base import *
from BaseOperate.CSVOperate import *
from BaseOperate.BaseOperate import *

def LogLink(headNode):
	handlesList = headNode.getHandlesList()
	for fieldName in handlesList:
		linkNode = headNode.getHandleLinkNode(fieldName)
		if linkNode:
			print("{0} FieldName:{1} Link {2}".format(headNode, fieldName, linkNode))
			LogLink(linkNode)

# 获取类的实例 后续改成每个类取不同参数来初始化
def GetNodeInsByRule(nodeName, keyWord):
	#关键字转换为类 String对应ValueNode  Add、Equal对应OperateNode
	cls = BaseNode.SubNodeClassDic.get(nodeName)
	if cls is None:
		cls = globals()[nodeName]
		BaseNode.SubNodeClassDic.setdefault(nodeName, cls)
		# 如何兼容多个文件定义的类？
	if cls:
		# 前两个字段寻找实例对象 (字面量Int、String的实例名就是其值)
		# 实例名一般用int类型来区分是否省略实例名
		# 部分特殊结点 实例名不为int
		moveStep = cls.getInsMoveStepByRule(keyWord)#默认0或1 代表可省略实例名
		# 子类的初始化参数不同 如何统一？？？
		instanceName = None
		if moveStep != 0:
			instanceName = keyWord
		nodeIns = BaseNode.getNodeInstance(nodeName, instanceName)
		if nodeIns is None:
			# Log("new cls instance !!! cls:{0} nodeName:{1} instanceName:{2}".format(cls, nodeName, instanceName))
			nodeIns = cls(nodeName, instanceName)#统一结点的初始化参数
		nodeIns.setMoveStep(moveStep)
		return nodeIns
	else:
		print("GetNodeInsByRule nodeName:{0} keyWord:{1} error".format(nodeName, keyWord))

def initByRule(ruleList, headNodeName):
	print("initRule start!!!!!")
	# 每个节点定义了参数个数 可有默认参数值
	headNode = None
	for rule in ruleList:
		index = 0
		maxIndex = len(rule)
		lastNode = None
		lastFieldName = None
		nodeIns = None
		fieldName = None
		while index < maxIndex:
			keyWord = None
			if rule[index] == "Bind":
				index = index + 1
				keyWord = "Bind"
			elif rule[index] == "Link":
				index = index + 1
				keyWord = "Link"
			ruleKey = rule[index]
			instanceName = None
			if index+1 < maxIndex:
				instanceName = rule[index+1]
			nodeIns = GetNodeInsByRule(ruleKey, instanceName)
			moveStep = nodeIns.getMoveStep()#0或1 是否省略instanceName
			print("ruleKey:{0} instanceName:{1} moveStep:{2}".format(ruleKey, instanceName, moveStep))
			index = index + moveStep + 1

			# 上一个结点的fieldName 可推算出 "Bind" or "Link"
			if keyWord == "Bind":#需要fieldName 即使其可能为空
				fieldNameList = []
				if index < maxIndex:
					fieldNameList = rule[index:]
				# else:#无参数 代表fieldName为空 采取默认值
				# 	pass
				fieldName = nodeIns.getFieldByRule(fieldNameList)
				moveStep = nodeIns.getMoveStep()#代表消耗的关键字
				index = index + moveStep
				print("Bind\nnode:{0} fieldName:{1} Bind node:{2} fieldName:{3}".format(lastNode, lastFieldName, nodeIns, fieldName))
				nodeSlot = lastNode.getRetNodeSlot(lastFieldName)
				nodeIns.bindArgNodeSlot(fieldName, nodeSlot)
			elif keyWord == "Link":#不需要fieldName
				if headNodeName is None:
					headNodeName = lastNode.nodeName
					headNode = lastNode
					print(headNode)
					print(headNodeName)
				print("Link\nnode:{0} fieldName:{1} Link node:{2}".format(lastNode,lastFieldName,nodeIns))
				lastNode.linkNodeField(lastFieldName, nodeIns)
			else:
				fieldNameList = []
				if index < maxIndex:
					fieldNameList = rule[index:]
				# else:#无参数 代表fieldName为空 采取默认的
				# print("not arg to getFieldByRule!!!")
				fieldName = nodeIns.getFieldByRule(fieldNameList)
				moveStep = nodeIns.getMoveStep()
				index = index + moveStep

			if headNode is None and nodeIns.nodeName == headNodeName:
				headNode = nodeIns
			lastNode = nodeIns
			lastFieldName = fieldName

	print("initByRule end!!!!!!! headNodeName:{0}".format(headNodeName))
	if headNode:
		LogLink(headNode)
	return headNode

class RuleGraph:
	def __init__(self, ruleList, headNodeName = None):
		self.graphNode = initByRule(ruleList, headNodeName)

	def run(self):
		if self.graphNode:
			self.graphNode.run()

#函数一个入口 多个结点可连接出口
def runRuleList(ruleList, headNodeName, instanceName, linkEndNodeList):
	funcRuleList = []
	funcRuleList.append(CompositeNode.LinkStartNodeRule(headNodeName, instanceName))
	funcRuleList.extend(ruleList)
	for nodeInsTuple in linkEndNodeList:
		nodeName = nodeInsTuple[0]
		instanceName = nodeInsTuple[1]
		fieldName = nodeInsTuple[2]
		funcRuleList.append(CompositeNode.LinkEndNodeRule(nodeName, instanceName, fieldName))
	mainFuncNode = CompositeNode("ATMain",None)
	print("funcRuleList:{0}".format(funcRuleList))
	headNode = initByRule(funcRuleList, headNodeName)
	if headNode:
		headNode.run()
	else:
		print("runRuleList() headNode is None")
	pass

def testRuleFunc():
	# 函数定义   未实现
	ruleList = []
	ruleList.append(["List","2","min","max","Bind","NewNode","Composite","GetRange","Args"])
	ruleList.append(["List","1","rangeList","Bind","NewNode","Composite","GetRange","Rets"])
	ruleList.append(["Int","1","Bind","GetRange","min"])
	ruleList.append(["Int","3","Bind","GetRange","max"])
	return ruleList

def main(*args,**kwargs):
	ruleList = []
	ruleList.append(["CSVData","BagChildUnlockTable","UnlockCondition","Bind","ForArray","List"])
	ruleList.append(["ForArray","Loop","Link","Branch"])
	ruleList.append(["ForArray","Value","Bind","Equal",1,"Left"])
	ruleList.append(["String","1","Bind","Equal",1,"Right"])
	ruleList.append(["Equal",1,"Bind","Branch","Condition"])
	ruleList.append(["Branch","True","Link","GetListValueByIndex"])
	ruleList.append(["CSVData","BagChildUnlockTable","Parm1","Bind","GetListValueByIndex","List"])
	ruleList.append(["ForArray","Index","Bind","GetListValueByIndex","Index"])
	ruleList.append(["GetListValueByIndex","Bind","GetListIndexByValue","Value"])
	ruleList.append(["GetListValueByIndex","Next","Link","GetListIndexByValue"])
	ruleList.append(["CSVData","CommonItemTable","ItemID","Bind","GetListIndexByValue","List"])
	ruleList.append(["GetListIndexByValue","Bind","Equal",2,"Left"])
	ruleList.append(["ValueNode",-1,"Bind","Equal",2,"Right"])
	ruleList.append(["GetListIndexByValue","Next","Link","Branch",1])
	ruleList.append(["Equal",2,"Bind","Branch",1,"Condition"])
	# ruleList.append(["String","True","Bind","PrintString",1,"String"])
	# ruleList.append(["Branch",1,"False","Link","PrintString",1])
	ruleList.append(["GetListValueByIndex","Bind","PrintString",2,"String"])
	ruleList.append(["Branch",1,"True","Link","PrintString",2])
	# runRuleList(ruleList,"ForArray",None,[("PrintString",1,"Next"),("PrintString",2,"Next"),("Branch",None,"False")])
	# headNode = initByRule(ruleList,None)
	# headNode.run()
	graphNode = RuleGraph(ruleList, None)
	graphNode.run()

	# 改进一
	# 采用渐进式的run 放弃原有的链式自动Run 对于部分复用结点可省略实例名 比如操作结点
	# 改进二
	# 错误输出内容 避免错误信息相同样式但需要反复定义 比如GetListIndexByValue、GetListValueByIndex 默认找不到对应的就应该错误提示并中断
	# 改进三
	# 整条检测链的最后逻辑类似 对比数据获取判断结果 即Branch结尾
	# 改进四
	# 复用结点与独立结点的判断 独立结点必然重复绑定参数  直接省略实例名
	# 改进五
	# 结点的默认关键字 希望能针对不同情况才采用多样式的 关键字与Link Bind重复
	# 改进六
	# 关键字 Bink Link可省略其一
	# todo
	# 规则定义推理函数 返回完整定义的规则链 暂时省略自定义函数
	pass

# if __name__ == "__main__":
# 	main()
