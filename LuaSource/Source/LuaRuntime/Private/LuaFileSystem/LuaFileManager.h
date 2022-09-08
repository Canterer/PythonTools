#pragma once
#include "ILuaFile.h"
#include "slua.h"
class FLuaFileManager : public TSharedFromThis<FLuaFileManager>
{
public:
	FLuaFileManager();
	void Init(NS_SLUA::lua_State * inL);
	bool LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & OutFilePath);
private:
	TSharedPtr<ILuaFile> LuaFile;
};
