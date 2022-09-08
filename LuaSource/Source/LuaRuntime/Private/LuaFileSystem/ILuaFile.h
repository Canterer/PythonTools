#pragma once
#include "CoreMinimal.h"
#include "slua.h"
DECLARE_LOG_CATEGORY_EXTERN(LuaFile, Log, All);

class ILuaFile : public TSharedFromThis<ILuaFile>
{
public:
	
	virtual bool LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath) = 0;

	virtual bool Initialize(NS_SLUA::lua_State * inL) = 0;
	virtual ~ILuaFile() {}
};
