import os
import sys
	
def merge_to_mp4(dest_file, source_path,file_list, delete, merge_flag):
	dest_file = os.path.join("D:/FFmpeg/",dest_file)# 修改为临时存放地址
	folderPath = os.path.dirname(dest_file)
	print("folderPath:",folderPath)
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)
	if merge_flag == False and os.path.exists(dest_file):
		print("merge_to_mp4 {0} is exists!!! skip".format(dest_file))
		return
	with open(dest_file, 'wb') as fw:
		for file_name in file_list:
			with open(source_path+"/"+file_name, 'rb') as fr:
				fw.write(fr.read())
	print("merge_to_mp4 {0} finished".format(dest_file))

def main(*args):
	print("args:",*args)
	folder_path = False
	replaceType = ".ts"
	argsNum = len(args)
	if argsNum == 0:
		print("not known folder_path!!!")
		return
	if argsNum >= 1:
		folder_path = args[0]

	if not os.path.isabs(folder_path):
		folder_path = os.path.join(os.getcwd(), folder_path)

	m3u8Path = os.path.join(folder_path, "_index.m3u8")
	temp_m3u8Path = os.path.join(folder_path, "_index.temp.m3u8")
	if not os.path.exists(m3u8Path):
		print("not find m3u8 file in path:",m3u8Path)
		return

	content = ""
	file_list = []
	with open(m3u8Path, "r", encoding="utf-8") as file:
		for line in file:
			if len(line) > 1 and line[0] != "#":
				startIndex = line.rfind("/")
				print("filename=",line[startIndex+1:-1])
				file_list.append(line[startIndex+1:-1])

	
	dest_file = folder_path[-5:]+"_out.mp4"
	print("dest_file ",dest_file)
	merge_to_mp4(dest_file, folder_path,file_list, False, True)


if __name__ == "__main__":
	main(*sys.argv[1:])
