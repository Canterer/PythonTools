import os

from BaseCore.BaseNode import *
from Operate.BaseOperate import *
from Operate.CSVOperate import *


def LogLink(headNode):
		handlesList = headNode.getHandlesList()
		for fieldName in handlesList:
			linkNode = headNode.getHandleLinkNode(fieldName)
			if linkNode:
				print("{0} FieldName:{1} Link {2}".format(headNode,fieldName,linkNode))
				LogLink(linkNode)

# 获取类的实例  后续改成每个类取不同参数来初始化
def GetNodeInsByRule(nodeName, keyWord):
	# 关键字转换为类   String对应ValueNode Add、Equal对应OperateNode
	cls = BaseNode.subNodeClassDic.get(nodeName)
	moveStep = 0
	if cls is None:
		cls = globals()[nodeName]
		BaseNode.subNodeClassDic.setdefault(nodeName, cls)
		# 如何兼容多个文件定义的类??
	if cls:
		# 前两个字段寻找实例对象  (字面量Int、String的实例名就是其值)
		# 实例名一般用int类型来区分是否省略实例名
		# 部分特殊结点  实例名不为int
		moveStep = cls.getInsMoveStepByRule(keyWord)#默认0或1 代表可省略的实例名
		# # 子类的初始化参数不同 如何统一？？？？
		instanceName = None
		if moveStep != 0:
			instanceName = keyWord
		nodeIns = BaseNode.getNodeInstance(nodeName, instanceName)
		if nodeIns is None:
			# Log("new cls instance ! cls:{0} nodeName:{1} instanceName:{2}".format(cls, nodeName, instanceName))
			nodeIns = cls(nodeName,instanceName)#统一结点的初始化参数
		nodeIns.setMoveStep(moveStep)
		return nodeIns
	else:
		print("GetNodeInsByRule nodeName:{0} keyWord:{1} error".format(nodeName, keyWord))

def initByRule(ruleList, headNodeName):
		print("initByRule start!!!!!!! headNodeName:{0}".format(headNodeName))
		# 每个节点定义了参数个数 可有默认参数值
		HeadNode = None
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
				# print("keyWord:{0} index:{1} maxIndex:{2}".format(keyWord, index, maxIndex))
				# 上一个节点的fieldName 可推算出"Bind" or "Link"
				if keyWord == "Bind":#需要fieldName 即使其可能为空
					fieldNameList = []
					if index < maxIndex:
						fieldNameList = rule[index:]
					# else:#无参数 代表fieldName为空 采取默认的
					# 	print("not arg to getFieldByRule!!!")
					fieldName = nodeIns.getFieldByRule(fieldNameList)
					moveStep = nodeIns.getMoveStep()#0或1 消耗的参数
					index = index + moveStep
					print("Bind\nnode:{0} fieldName:{1} Bind node:{2} fieldName:{3}".format(lastNode, lastFieldName, nodeIns, fieldName))
					nodeSlot = lastNode.getRetNodeSlot(lastFieldName)
					nodeIns.bindArgNodeSlot(fieldName, nodeSlot)
				elif keyWord == "Link":#不需要fieldName
					if headNodeName is None:
						headNodeName = lastNode.nodeName
						HeadNode = lastNode
						print(HeadNode)
						print(headNodeName)
					print("Link\nnode:{0} fieldName:{1} link node:{2}".format(lastNode, lastFieldName, nodeIns))
					lastNode.linkNodeFiled(lastFieldName, nodeIns)
				else:
					fieldNameList = []
					if index < maxIndex:
						fieldNameList = rule[index:]
					# else:#无参数 代表fieldName为空 采取默认的
					# 	print("not arg to getFieldByRule!!!")
					fieldName = nodeIns.getFieldByRule(fieldNameList)
					moveStep = nodeIns.getMoveStep()#0或1 消耗的参数
					index = index + moveStep

				if HeadNode is None and nodeIns.nodeName == headNodeName:
					HeadNode = nodeIns

				lastNode = nodeIns
				lastFieldName = fieldName
		print("initByRule end!!!!!!! headNodeName:{0}".format(headNodeName))
		if HeadNode:
			LogLink(HeadNode)
		return HeadNode

# 函数一个入口 多个节点可连接出口
def runRuleList(ruleList, headNodeName, headNodeInsName, linkEndNodeList):
	funcRuleList = []
	funcRuleList.append(Composite.LinkStartNode(headNodeName,headNodeInsName))
	funcRuleList.extend(ruleList)
	for nodeInsTuple in linkEndNodeList:
		nodeName = nodeInsTuple[0]
		instanceName = nodeInsTuple[1]
		fieldName = nodeInsTuple[2]
		funcRuleList.append(Composite.LinkEndNode(nodeName,instanceName,fieldName))
	mainFuncNode = Composite("ATTmain",None)
	print("funcRuleList:",funcRuleList)
	headNode = initByRule(funcRuleList,headNodeName)
	if headNode:
		headNode.run()
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
	# OperateNode("Add")
	# OperateNode("Not")
	# OperateNode("And")
	# OperateNode("Equal")
	# OperateNode("Less")


	ruleList = []
	ruleList.append(["CSVData","BagChildUnlockTable","UnlockCondition","Bind","ForArray","List"])
	ruleList.append(["ForArray","Loop","Link","Branch"])
	ruleList.append(["ForArray","Value","Bind","Equal",1,"Left"])
	ruleList.append(["String","1","Bind","Equal",1,"Right"])
	ruleList.append(["Equal",1,"Bind","Branch","condition"])
	ruleList.append(["Branch","True","Link","GetListValueByIndex"])
	ruleList.append(["CSVData","BagChildUnlockTable","Parm1","Bind","GetListValueByIndex","List"])
	ruleList.append(["ForArray","Index","Bind","GetListValueByIndex","Index"])
	ruleList.append(["GetListValueByIndex","Bind","GetListIndexByValue","Value"])
	ruleList.append(["GetListValueByIndex","Next","Link","GetListIndexByValue"])
	ruleList.append(["CSVData","CommonItemTable","ItemID","Bind","GetListIndexByValue","List"])
	ruleList.append(["GetListIndexByValue","Bind","Equal",2,"Left"])
	ruleList.append(["ValueNode",-1,"Bind","Equal",2,"Right"])
	ruleList.append(["GetListIndexByValue","Next","Link","Branch",1])
	ruleList.append(["Equal",2,"Bind","Branch",1,"condition"])
	# ruleList.append(["String","True","Bind","PrintString",1,"String"])
	# ruleList.append(["Branch",1,"False","Link","PrintString",1])
	ruleList.append(["GetListValueByIndex","Bind","PrintString",2,"String"])
	ruleList.append(["Branch",1,"True","Link","PrintString",2])
	# runRuleList(ruleList,"ForArray",None,[("PrintString",1,"Next"),("PrintString",2,"Next"),("Branch",None,"False")])
	headNode = initByRule(ruleList,None)
	headNode.run()

	pass
	# 改进一
	# 采用渐进式的run 放弃原有的链式自动run  对于部分复用节点可省略实例名 比如操作节点

	# 改进二
	# 错误输出内嵌 避免错误信息相同样式但是反复定义 比如GetListIndexByValue、GetListValueByIndex 默认找不到对应的就应该错误提示并中断

	# 改进三
	# 整条检测链的最后逻辑结构类似  对比数据获取判断结果 即Branch结尾

	# 改进四
	# 复用节点与独立节点的判断  独立节点必然重复绑定参数  直接省略实例名

	# 改进五
	# 节点的默认关键字 希望能针对不同情况采取多样式的  关键字与Link Bind重复

	# 改进六
	# 关键字 Bink Link 可省略其一

	# todo
	# 规定定义推理函数 返回完整定义的规则链 暂时省略自定义函数

if __name__ == "__main__":
	# from Run import *
	main() 