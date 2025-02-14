import os
import re

def GetBracketRange(content,leftChar,rightChar):
	leftCharCount = 0
	rightCharCount = 0

	leftIndex = 0
	rightIndex = len(content)-1
	index = 0
	endIndex = len(content)
	while index < endIndex:
		char = content[index]
		if char == rightChar:
			print("wrong bracket style! find rightChar first")
			return (0,0)
		elif char == leftChar:
			leftCharCount = 1
			leftIndex = index
			index+=1
			break
		index+=1
	while index < endIndex and leftCharCount != rightCharCount:
		char = content[index]
		if char == leftChar:
			leftCharCount = leftCharCount + 1
		elif char == rightChar:
			rightCharCount = rightCharCount + 1
		# print(char,leftCharCount,rightCharCount)
		index+=1
		if leftCharCount < rightCharCount:
			print("wrong bracket style! leftCharCount={0} < rightCharCount={1}".format(leftCharCount,rightCharCount))
			return (0,0)
		else:
			rightIndex = index#更新结束位置
		
	if leftCharCount == rightCharCount:
		# print("GetBracketRange end:",content,content[leftIndex:rightIndex])
		return (leftIndex,rightIndex)
	else:
		print("wrong bracket style! find all leftCharCount={0} > rightCharCount={1}".format(leftCharCount,rightCharCount))
		return (0,0)
	

def GetValueByContent(content):
	content = re.sub("\s","",content)#去除空白符

	if content[0] != "{" or content[-1] != "}":
		print("content isn't table:",content)
		return
	content = content[1:-1]#去除前后{}

	table = {}
	listCount = 1#数组可装填的序号
	index = 0
	endIndex = len(content)
	while  index < endIndex:
		# print("next content:",content[index:])
		result = re.match("([^,=\{\}]+)",content[index:])
		if result:# "value" or "key=..."
			match = result.group(1)
			index = result.span()[1]+index
			if index == endIndex:#"value"最后一个值
				print("match word:",match)
				table[listCount] = match
				# break
			elif content[index] == ",":#"value,"
				print("match word:",match)
				table[listCount] = match
				listCount+=1
				index+=1
			elif content[index] == "=":#"key=..."
				index+=1
				result = re.match("([^,=\{\}]+)",content[index:])
				if result:#",key=value,"
					value = result.group(1)
					table[match]=value
					print("match KV: {0}={1}".format(match,value))
					index = result.span()[1]+index
				else:#"key={...}"
					# print("key=...",content[index:])
					if re.match("\{(.*)\}",content[index:]):
						bracketRange = GetBracketRange(content[index:],"{","}")
						startPos = bracketRange[0]+index
						endPos = bracketRange[1]+index
						print("key={...}: "+"{0}={1}".format(match,content[startPos:endPos]))
						table[match]=GetValueByContent(content[startPos:endPos])
						index = endPos
					else:
						print("sub table wrong style:",content[index:])
						return
			else:
				print("wrong style:",match,content[index:])
				return
		else:# "{...}"
			# print("{...}[,}]...:",content[index:])
			if re.match("\{(.*)\}",content[index:]):
				bracketRange = GetBracketRange(content[index:],"{","}")
				startPos = bracketRange[0]+index
				endPos = bracketRange[1]+index
				# print("{...}:",content[startPos:endPos])
				table[listCount]=GetValueByContent(content[startPos:endPos])
				listCount+=1
				index = endPos
			else:
				print("sub table wrong style:",content[index:])
				return

		if index < endIndex and content[index] == ",":
			index+=1

	# if index == endIndex:
	# 	print("wrong table style")
	# 	return
	return table

def main(*args,**kwargs):
	line = """{
	target = targetValue,
	table = {
		elementT = {
			a = a,
			b = b,
			c
		},
		list = {
			a,
			b,
			c
		}
	},
	tar = tarValue,
	list = {
		b,
		c,
		d
	},
	other = {1}
}"""
	# line = "{a=b,{b=c}}"
	# bracketRange = GetBracketRange(line,"{","}")
	# startPos = bracketRange[0]
	# endPos = bracketRange[1]
	# print("bracketContent:",line[startPos:endPos])
	print("test serialize table:",re.sub("\s","",line))
	table = GetValueByContent(line)
	print("test table:",table)
	
	
if __name__ == '__main__':
	main()   