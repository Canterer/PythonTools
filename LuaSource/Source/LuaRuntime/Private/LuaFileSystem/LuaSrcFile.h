#pragma once 
#include "ILuaFile.h"

class FLuaSrcFile :public ILuaFile
{
public:
	bool LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath) override;

	static bool IsExists(FString const & InFilePath);
	bool Initialize(NS_SLUA::lua_State * inL) override;

	static bool IsEnable();

	static FString MakeAbsFilePath(FString const & InFilePath);

	static FString BaseDir();

	virtual ~FLuaSrcFile();
};
