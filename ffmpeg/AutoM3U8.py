#!/usr/bin/python

import os
import sys
import getopt

ffmpegExePath = ""#"D:/WorkSpaces/SoftSpaces/ffmpeg/bin/ffmpeg.exe"
masterName = "rep.m3u8"
# inputRootDir = "C:\\Users\\Administrator\\Desktop\\HLS_Spaces\\input"
outputRootDir = ""#"C:\\Users\\Administrator\\Desktop\\HLS_Spaces\\output"
outputSubDir = "segment"
outputFileName = "req_%v_.m3u8"
segment_type_ts = "mpegts"
segment_type_m4s = "fmp4"

DefaultVideoBite = 1
DefaultMaxRate = 1.5
DefaultMinRate = 0

def getCmd(inputFileName, outputSubDir, segment_type_flag, RateScale):
    if inputFileName[-4:] != ".mp4":#仅输入文件名 不带后缀 默认当前目录
        inputFileName = inputFileName + ".mp4"
    
    inputFilePath = ""
    dirname = os.path.dirname(inputFileName)
    if dirname == "":
        inputFilePath = os.path.join(os.getcwd(), inputFileName)
    else:
        inputFilePath = inputFileName
    basename = os.path.basename(inputFileName)
    if outputSubDir is None:
        outputSubDir = basename.rsplit('.',1)[0]
    if RateScale is None:
        RateScale = 1
    return runCmd(inputFilePath, outputSubDir, segment_type_flag, RateScale*DefaultVideoBite, RateScale*DefaultMaxRate, RateScale*DefaultMinRate)

def runCmd(inputFilePath, outputSubDir, segment_type_flag, videoBite=DefaultVideoBite, maxRate=DefaultMaxRate, minRate=DefaultMinRate):
    print("runCmd args:\n inputFilePath:{0} outputSubDir:{1} segment_type_flag:{2} videoBite:{3} maxRate:{4} minRate:{5}".format(inputFilePath, outputSubDir, segment_type_flag, videoBite, maxRate, minRate))
    VideoBiteStr = str.format(" -b:v {0}M -maxrate:v {1}M -minrate:v {2}M -bufsize:v {3}M ", videoBite, maxRate, minRate, 2*maxRate)
    cmdStr = ffmpegExePath + " -i " + inputFilePath
    cmdStr = cmdStr + " -map v:0 " + VideoBiteStr
    cmdStr = cmdStr + " -map a:0 -c:a:0 copy"
    hls_segment_type = segment_type_ts if segment_type_flag else segment_type_m4s
    hlsControlStr = str.format(" -hls_list_size 0 -hls_segment_type {0} -f hls -master_pl_name {1} ", hls_segment_type, masterName)
    cmdStr = cmdStr + hlsControlStr
    cmdStr = cmdStr + " -var_stream_map \"v:0,agroup:720_group a:0,agroup:720_group\" "
    folderPath = os.path.join(outputRootDir,outputSubDir,hls_segment_type)
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    cmdStr = cmdStr + os.path.join(folderPath,outputFileName)
    print("cmd: "+cmdStr)    
    cmdStr = "cd {0} && {1}".format(folderPath, cmdStr)
    return cmdStr

def main(argv):
    # 
    global ffmpegExePath,outputRootDir
    ffmpegExePath = os.path.join(os.getcwd(), "ffmpeg.exe")
    outputRootDir = os.path.join(os.getcwd(), "output")

    inputFileName=outputSubDir=segment_type_flag=rateScale=None
    inputFileName=argv[0]
    
    shortArgsStr = "i:f:r:"
    longArgsList = ["outputSubDir=","segement_type_flag=","rateScale=","outputRootDir=","ffmpegExePath=","help"]
    opts, args = getopt.getopt(argv,shortArgsStr,longArgsList)
    for opt, value in opts:
        if opt == "-i":
            inputFileName = value
        elif opt == "--outputSubDir":
            outputSubDir = value
        elif opt == "--outputRootDir":
            outputRootDir = value
        elif opt == "--ffmpegExePath":
            ffmpegExePath = value
        elif opt in ("-f","--segement_type_flag"):
            segment_type_flag = value
        elif opt in ("-r","--rateScale"):
            rateScale = value
        elif opt == "--help":
            print("shortArgsStr:",shortArgsStr)
            print("longArgsList:")
            for arg in longArgsList:
                print("\t--"+arg)
            return

    print("argv:",*argv)
    print("ffmpeg Path:",ffmpegExePath)
    print("output Path:",outputRootDir)

    if inputFileName is None:
        print("inputFileName is need!!!")
        print(len(args))
        return

    if segment_type_flag is None:
        cmdStr = getCmd(inputFileName,outputSubDir,False,rateScale)
        os.system(cmdStr)
        cmdStr = getCmd(inputFileName,outputSubDir,True,rateScale)
        os.system(cmdStr)
    else:
        cmdStr = getCmd(inputFileName,outputSubDir,segment_type_flag,rateScale)
        os.system(cmdStr)


if __name__ == "__main__":
    main(sys.argv[1:])

# if __name__ == "__main__":
#     main(*sys.argv[1:])

# def main(*args, **kwargs):
#     print("args:",args," kwargs:",kwargs)
#     print("args len:", len(args))

#     firstOpt = args[0]
#     callFunc(*args[1:])#不定参数 可触发函数默认值
    
