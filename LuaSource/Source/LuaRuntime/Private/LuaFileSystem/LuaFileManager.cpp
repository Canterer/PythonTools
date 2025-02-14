#include "LuaFileSystem/LuaFileManager.h"

#include "LuaFileSystem/LuaSrcFile.h"
#include "LuaFileSystem/LuaServerFile.h"
#include "LuaFileSystem/ILuaFile.h"
#include "LuaFileSystem/LuaPakFile.h"

FLuaFileManager::FLuaFileManager()
{
}

void FLuaFileManager::Init(NS_SLUA::lua_State * inL)
{

#if PLATFORM_WINDOWS || PLATFORM_ANDROID || PLATFORM_IOS
	if(FLuaSrcFile::IsEnable())
	{
		LuaFile = MakeShareable(new FLuaSrcFile);
	}
	else
	{
		LuaFile = MakeShareable(new FLuaPakFile);
	}
#else
	LuaFile = MakeShareable(new FLuaPakFile);
#endif

	if(inL != nullptr)
	{
		LuaFile->Initialize(inL);
	}
}

bool FLuaFileManager::LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & OutFilePath)
{
	if(LuaFile.IsValid())
	{
		return LuaFile->LoadFileContent(fn,OutContent,OutFilePath);
	}

	return false;
}
