import stat,os

def getFilesByFolder(folder):
	folderPath = os.path.join(os.getcwd(),folder)
	filePathList = []
	for root,dirs,files in os.walk(folderPath):
		for file in files:
			filePathList.append(os.path.join(root,file))
	return filePathList
	
def main(*args,**kwargs):
	print("run main")
	filePathList = getFilesByFolder("LuaSource")
	for filePath in filePathList:
		print(filePath)
		if os.path.isfile(filePath):
			os.chmod(filePath, stat.S_IRWXU)
			os.remove(filePath)
			#print(filePath)
			with open(filePath,mode="w",encoding="utf-8-sig",errors="ignore") as f:
				#f.write("")
				print(filePath)

if __name__ == "__main__":
	# from Run import *
	main() 