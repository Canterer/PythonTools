#pragma once
#include "ILuaFile.h"
class FLuaPakFile : public ILuaFile
{
public:
	~FLuaPakFile();
	virtual bool LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath) override;

	virtual bool IsExists(FString const & InFilePath);
	virtual bool Initialize(NS_SLUA::lua_State * inL);

	static bool IsEnable();

	static int32 loadfile();
public:
	FString MakeLuaObjPath(FString const & InFilePath);
};
