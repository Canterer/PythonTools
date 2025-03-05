import os
import sys
 
def rename_files_in_folder(folder_path, old_suffix, new_suffix):
    for filename in os.listdir(folder_path):
        if filename.endswith(old_suffix):
            os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, filename.replace(old_suffix, new_suffix)))
 

def main(*args):
	print("args:",*args)
	url = args[0]#"https://index.m3u8"
	folder_path = False
	
	fileType = ".jpeg"
	replaceType = ".ts"
	replaceFlag = True
	argsNum = len(args)
	if argsNum == 0:
		print("not known folder_path!!!")
		return
	if argsNum >= 1:
		folder_path = args[0]
	if argsNum >= 2:
		replaceFlag = args[1]=="True" or args[1]=="1"
	if argsNum >= 3:
		fileType = args[2]

	if not os.path.isabs(folder_path):
		folder_path = os.path.join(os.getcwd(), folder_path)

	m3u8Path = os.path.join(folder_path, "_index.m3u8")
	if not os.path.exists(m3u8Path):
		print("not find m3u8 file in path:",m3u8Path)
		return

	content = ""
	findStr = replaceFlag and fileType or replaceType
	replaceStr = replaceFlag and replaceType or fileType
	print("replaceFlag:{0} {1}=>{2}".format(replaceFlag, findStr, replaceStr))
	findStrLen = len(findStr)+1
	with open(m3u8Path, "r", encoding="utf-8") as file:
		for line in file:
			if len(line) > findStrLen and line[-findStrLen:-1] == findStr:
				line = line[:-findStrLen] + replaceStr + "\n"
			content += line
	with open(m3u8Path, "w", encoding="utf-8") as file:
		file.write(content)

	rename_files_in_folder(folder_path, findStr, replaceStr)


if __name__ == "__main__":
	main(*sys.argv[1:])