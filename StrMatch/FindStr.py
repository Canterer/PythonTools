#!/usr/bin/python
import os
import sys
import re

def main(*args):
    inputFile = "results.txt"
    outputFile = "output.txt"
    if len(args) == 1:
        inputFile = args[0]
    curDir = os.getcwd()
    inputFilePath = os.path.join(curDir, inputFile)
    outputFilePath = os.path.join(curDir, outputFile)
    inputContent = ""
    if not os.path.exists(inputFilePath):
        print("not find input file:",inputFilePath)
        return
    else:
        print("input file path:",inputFilePath)
    
    with open(inputFilePath, "r", encoding="utf-8") as f:
        for line in f:
            inputContent += line

    result = re.findall("(std::\w+)", inputContent)
    resultContentList = list(set(result))
    resultContentList.sort()
    # print("input path:",inputFilePath)
    print("result line total:",len(resultContentList))
    if not os.path.exists(outputFilePath):
        os.makedirs(outputFilePath)
    with open(outputFilePath, "w", encoding="utf-8") as f:
        for funcStr in resultContentList:
            f.write(funcStr+"\n")

    os.system(outputFilePath)


if __name__ == "__main__":
    main(*sys.argv[1:])
