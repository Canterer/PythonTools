import os
from BaseCore.BaseGraph import *

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


if __name__ == "__main__":
	main()
