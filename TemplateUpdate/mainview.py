#!usr/bin/python
import os
import sys
import re

'''
	每个组件插入Code  三种基本情况  每条rule可能多个情况混合
		特定函数同类型代码后插入(新增代码)
		插入特定函数后固定代码(新增函数)
		写入特定模板(新增文件)
'''
class BaseComponent:
	#以下Re使用match匹配字符串开头
	_anyFuncRe = re.compile("function (.*)?:")
	_exitFuncRe = re.compile("end")
	_returnFileRe = re.compile("return .*")
	_instanceList = {}#每个组件的单例对象

	_componetMatchlist = {}#各组件匹配的关键字列表
	def __init__(self,componetRuleName):
		self.state = 1#状态机初始量 0代表退出匹配  1代表未进入匹配  其他代表该规则的匹配状态
		self.ruleKeyList = []#原始的规则列表 从Component规则文件中直接解析出来
		self.ruleList = []#规则列表 每条规则对应一行插入文本
		self.codeList = []#插入Code列表
		# self.reList = []#正则匹配列表
		self.valuesList = []#实例数据列表 记录每个实例的关键字信息  派生类使用单例模式存储多个实例的关键字信息

		self.runningRule = None#正在匹配中的规则
		self.ruleFlagList = {}#记录规则是否匹配过 存储序号
		self.componetRuleName = componetRuleName
		self.initComponetFile(componetRuleName)
		self.initRuleList()

	def initComponetFile(self,componetRuleName):
		print("Init componetRuleName:",componetRuleName)
		with open(os.path.join(os.getcwd(),"Template",componetRuleName+".rule"),mode="r",encoding="utf-8",errors="ignore") as f:
			# for line in f.readlines():
			LastRuleKey = None
			for line in f:
				line = line.partition("#")[0]#去除注释
				if not LastRuleKey:#兼容插入空白行
					line = line.strip(" \n\t")#去除空白字符
					if len(line) == 0: continue

				group = line.partition(":")#开分每条规则
				ruleKey = group[0]
				ruleValues = group[2]

				if LastRuleKey:#列表元素的ruleKey是数字
					if LastRuleKey == "CodeList":
						if ruleKey.isnumeric():
							self.codeList.append("")
						else:
							self.codeList[-1] = self.codeList[-1] + line
					# elif LastRuleKey == "ReList":
					# 	self.reList.append(ruleValues)#插入代码列表或正则列表
				else:#处理插入
					if ruleValues == "":#该规则是列表,其元素在下几行
						LastRuleKey = ruleKey
					else:
						ruleValues = ruleValues[1:-1]#去除前后"[""]"
						ruleValues = ruleValues.split(":")
						self.ruleKeyList.append((ruleKey,ruleValues))

	def initRuleList(self):
		for index,rule in enumerate(self.ruleKeyList):
			ruleKey = rule[0]
			ruleValues = rule[1]

			funcName = ruleValues[0]
			funcNameRe = re.compile("function (.*)?:"+funcName)
			codeIndex = int(ruleValues[1])
			ruleReValues = []
			if ruleKey == "insertCode":
				codeLine = self.GetCodeByIndex(codeIndex)
				codeLine = codeLine.replace(".","\.")
				codeLine = codeLine.replace("(","\(")
				codeLine = codeLine.replace(")","\)")
				codeLine = codeLine.replace("<0>","(.*)?")#默认插入最多三个关键字
				codeLine = codeLine.replace("<1>","(.*)?")
				codeLine = codeLine.replace("<2>","(.*)?")
				codeRe = re.compile(codeLine)

				ruleReValues.append(funcNameRe)
				ruleReValues.append(codeRe)
				ruleReValues.append(codeIndex)
			elif ruleKey == "insertFunc":
				ruleReValues.append(funcNameRe)
				ruleReValues.append(codeIndex)

			self.ruleFlagList[index] = False
			self.ruleList.append((ruleKey,ruleReValues))

	def AddInsData(self,values):#存储实例的关键字信息
		self.valuesList.append(values)

	def ResetComponent(self):
		for index in self.ruleFlagList:
			self.ruleFlagList[index] = False#清除规则匹配记录
		self.valuesList = []#清除实例信息

	@staticmethod
	def getInstance(componetRuleName):#Component对应规则文件名
		if BaseComponent._instanceList.get(componetRuleName) is None:
			BaseComponent._instanceList[componetRuleName] = BaseComponent(componetRuleName)
		return BaseComponent._instanceList.get(componetRuleName)

	#定位函数
	@staticmethod
	def seekFunc(line,funcNameRe):#定位函数 假设函数空格布局严谨,"end"匹配函数结束
		line = line.partition("--")[0]#去除Lua注释
		if funcNameRe.match(line):#匹配字符串开头
			return True
		else:
			return False

	@staticmethod
	def seekCode(line,codeRe):#匹配单行插入代码
		if codeRe.search(line):
			return True
		else:
			return False

	@staticmethod
	def RecordMatch(componetRuleName, key):
		keyDic = BaseComponent._componetMatchlist.get(componetRuleName, {})
		keyDic[key] = True
		BaseComponent._componetMatchlist[componetRuleName] = keyDic
		# print("RecordMatch",componetRuleName,keyDic,key)

	@staticmethod
	def IsHasMatch(componetRuleName, key):
		keyDic = BaseComponent._componetMatchlist.get(componetRuleName, {})
		return keyDic.get(key) == True

	def RecordComponentInsertKey(self):
		for values in self.valuesList:
			BaseComponent.RecordMatch(self.componetRuleName, values[0])

	#插入函数
	def insertFunc(self,line,funcNameRe):
		if self.state == 0:#退出该规则匹配
			return
		if self.state == 1:#匹配同类函数
			if self.seekFunc(line,funcNameRe):
				# print("find Func",funcNameRe.match(line).group(2))
				BaseComponent.RecordMatch(self.componetRuleName, funcNameRe.match(line).group(2))
				self.state = 2
		elif self.state == 2:#匹配退出函数
			if self.seekFunc(line,BaseComponent._exitFuncRe):
				self.state = 3
		elif self.state == 3:#寻找插入时机
			if self.seekFunc(line,BaseComponent._anyFuncRe):#匹配到任何函数
				if self.seekFunc(line,funcNameRe):
					BaseComponent.RecordMatch(self.componetRuleName, funcNameRe.match(line).group(2))
					self.state = 2#再次匹配同类函数
				else:
					self.state = 0#匹配到非同类函数 准备插入
			elif self.seekCode(line,BaseComponent._returnFileRe):#匹配到文件退出 return XXX
				self.state = 0

	#插入代码
	def insertCode(self,line,funcNameRe,codeRe):
		if self.state == 0:#退出该规则匹配
			return
		if self.state == 1:#匹配特定函数
			if self.seekFunc(line,funcNameRe):
				self.state = 2
		elif self.state == 2:
			if self.seekFunc(line,BaseComponent._exitFuncRe):#匹配到退出函数 无同类Code
				self.state = 0
			else:
				if self.seekCode(line,codeRe):#匹配到同类Code
					# print("find code",codeRe.match(line).group(1))
					BaseComponent.RecordMatch(self.componetRuleName, codeRe.match(line).group(1))
					self.state = 3
				else:
					self.state = 2
		elif self.state == 3:#匹配非同类Code(包含函数退出)
			if not self.seekCode(line,codeRe):
				self.state = 0
			else:#匹配到同类Code 
				BaseComponent.RecordMatch(self.componetRuleName, codeRe.match(line).group(1))

	def initFileByTemplate(templateName,fd,replaceStr):
		templatePath = os.path.join(os.getcwd(),"Template",templateName+".lua")
		if not os.path.isfile(templatePath):
			print("template file can't find ! path:",templatePath)
			return
		with open(templatePath,mode="r") as f:
			for line in f:
				fd.write(line.replace("XXX",replaceStr))

	def CheckLine(self,line):
		# 所有规则同时仅一条规则处于运行中
		if self.runningRule != None:
			self.CheckLineWith(line,self.runningRule)
		else:
			for index,rule in enumerate(self.ruleList):#未匹配的插入列表
				if self.ruleFlagList[index] == False:
					self.CheckLineWith(line,rule)
					if self.state > 1:# 0代表退出匹配 1代表未匹配 其他为匹配中
						self.runningRule = rule
						self.ruleFlagList[index] = True
						break

	def CheckLineWith(self,line,rule):
		ruleKey = rule[0]
		ruleReValues = rule[1]
		funcNameRe = ruleReValues[0]
		if ruleKey == "insertCode":
			codeRe = ruleReValues[1]
			self.insertCode(line,funcNameRe,codeRe)
		elif ruleKey == "insertFunc":
			self.insertFunc(line,funcNameRe)

	def RunAndWrite(self,line,fb,):
		self.CheckLine(line)
		if self.state == 0:
			for values in self.valuesList:#某种component的实例数据列表
				if not BaseComponent.IsHasMatch(self.componetRuleName, values[0]):
					fb.write(self.GetInsertLine(values))				
			self.NextState()

	def GetRunningRule():
		return self.runningRule

	def GetInsertLine(self,values):
		if self.state == 0 and self.runningRule:
			ruleValues = self.runningRule[1]
			codeIndex = ruleValues[-1]
			code = self.GetCodeByIndex(codeIndex)
			keyLen = len(values)
			for i in range(0,keyLen):
				code = code.replace("<"+str(i)+">",values[i])
			return code

	def NextState(self):
		self.state = 1#重置状态为未匹配
		self.runningRule = None#置空 寻找下一个匹配上的规则

	def ResetState(self):
		self.state = 1#未匹配
		self.runningRule = None

	def GetCodeByIndex(self,index):
		return self.codeList[index]

	# def GetReByIndex(self,index):
	# 	return self.reList[index]

class RuleFile:
	# RootPath = "D:\\MMOFPS\\NZEditor-Dev\\NZMobile\\Plugins\\UnrealLua\\LuaSource\\frontend"
	RootPath = "Y:\\WorkSpaces\\PythonSpaces\\PythonTools\\ProjectRoot"

	def __init__(self,filePath):
		self.filePath = filePath#相对路径
		self.keyDic = {}#规则字典
		self.componetInsList = {}#组件实例字典
		self.absPath = os.path.join(os.getcwd(),filePath)
		if not os.path.isfile(self.absPath):
			print("rule path is error! path:",absPath)
			return

	def initRules(self):
		ModelName = None
		LastRuleKey = None
		with open(self.absPath,mode="r",encoding="utf-8",errors="ignore") as f:
			for line in f.readlines():
				line = line.strip(" \n\t")#去除空白字符
				line = line.partition("#")[0]#去除注释
				if len(line) == 0: continue
				group = line.partition(":")#开分每条规则
				key = group[0]
				value = group[2][1:-1]#去除前后"[""]"
				# if value == "":#上一条规则是列表
				# 	print("list element:",value)
				# 	self.keydic[LastRuleKey].append(value)
				# else:
				self.keyDic[key]=value

	@staticmethod
	def InitFileByTemplate(templateName,fd,replaceStr):
		templatePath = os.path.join(os.getcwd(),"Template",templateName+".lua")
		if not os.path.isfile(templatePath):
			print("template file can't find ! path:",templatePath)
			return
		with open(templatePath,mode="r") as f:
			for line in f:
				fd.write(line.replace("XXX",replaceStr))

	def initModel(self):
		ruleValues = self.keyDic["ModelName"].split(":")
		self.ModelTemplate = ruleValues[0]#模块模板名
		self.ModelNameMatch = ruleValues[1]#模块名 替换字符默认XXX
		self.ModelFileName = ruleValues[2]#模块文件名
		self.ModelFolder = ruleValues[3]#模块文件夹
		if "xxx" in self.ModelFileName:
			self.ModelFileName = self.ModelFileName.replace("xxx",self.ModelNameMatch.lower())
		if "xxx" in self.ModelFolder:
			self.ModelFolder=self.ModelFolder.replace("xxx",self.ModelNameMatch.lower())
		print(self.ModelTemplate,self.ModelNameMatch,self.ModelFileName,self.ModelFolder)

	def initComponents(self):
		for key in self.keyDic:
			if key != "ModelName":
				value = self.keyDic[key]
				componet = BaseComponent.getInstance(key)
				value = value.replace(",...",'')#去除省略号
				componetInstanceList = value.split(",")#组件实例列表
				for KeyValues in componetInstanceList:#组件实例 关键字组合
					valueList = KeyValues.split(":")#拆分成关键字列表
					componet.AddInsData(valueList)
				if self.componetInsList.get(key) is None:
					self.componetInsList[key] = componet

	def runComponent(self,componetIns):
		folderPath = os.path.join(RuleFile.RootPath,self.ModelFolder)
		if not os.path.exists(folderPath) :
			os.mkdir(folderPath)
		modelFilePath = os.path.join(folderPath,self.ModelFileName+".lua")
		modelTempFilePath = os.path.join(folderPath,self.ModelFileName+"_temp.lua")
		if not os.path.exists(modelFilePath):
			with open(modelFilePath,mode="w+",encoding="utf-8",errors="ignore") as f:
				RuleFile.InitFileByTemplate(self.ModelTemplate,f,self.ModelNameMatch)

		# 开始针对已生成文件进行代码插入
		with open(modelTempFilePath,mode="w",encoding="utf-8",errors="ignore") as tempFd:
			with open(modelFilePath,mode="r",encoding="utf-8",errors="ignore") as f:
				for line in f:
					componetIns.RunAndWrite(line,tempFd)#先写入插入内容
					tempFd.write(line)
				componetIns.RecordComponentInsertKey()#记录写入的关键字 防止重复写入
				componetIns.ResetComponent()#清空组件已写入的关键字

		os.remove(modelFilePath)
		os.rename(modelTempFilePath,modelFilePath)

	def run(self):
		for key in self.componetInsList:
			self.runComponent(self.componetInsList[key])

	def runCommand(self,command):
		group = command.partition(":")#拆分规则
		key = group[0]
		value = group[2][1:-1]#去除前后"[""]"
		componet = BaseComponent.getInstance(key)
		componet.ResetComponent()
		value = value.replace(",...",'')#去除省略号
		componetInstanceList = value.split(",")#组件实例列表
		for KeyValues in componetInstanceList:#组件实例 关键字组合
			valueList = KeyValues.split(":")#拆分成关键字列表
			componet.AddInsData(valueList)
		self.runComponent(componet)

def main(*args,**kwargs):
	ruleFile = RuleFile("Rule.txt")
	ruleFile.initRules()
	ruleFile.initModel()
	ruleFile.initComponents()
	ruleFile.run()
	commandRe = re.compile("(.*)?:\[(.*)\]")
	while True:
		command = input("run command or 空字符退出:")
		if command == "":
			break
		elif commandRe.match(command) is None:
			print("command is not right style: xx:[x:y,...]")
		else:
			ruleFile.runCommand(command)

def ListToDic(list):
	count = len(list)
	result = dict()
	for index in range(1,count,2):
		result[list[index-1]] = list[index]
	return result

if __name__ == '__main__':
	argsDic = ListToDic(sys.argv[1:])
	main(**argsDic)   