
#include "LuaFileSystem/LuaSrcFile.h"
#include "LuaFileSystem/LuaServerFile.h"
#include "LuaFileSystem/LuaPakFile.h"

#include "Misc/Paths.h"

#include "NetworkMessage.h"
#include "SocketSubsystem.h"
#include "IPAddress.h"
#include "LuaSetting.h"
#include "Sockets.h"
#include "MultichannelTcpSocket.h"

#include "HAL/PlatformFilemanager.h"
#include "Misc/App.h"

DEFINE_LOG_CATEGORY(LuaFile);

#if PLATFORM_ANDROID
extern FString GFilePathBase;
#define FILEBASE_DIRECTORY "/UE4Game/"
#endif


FLuaSrcFile::~FLuaSrcFile()
{

}
FString FLuaSrcFile::BaseDir()
{
	FString ResultFilePath;

#if PLATFORM_WINDOWS
#if WITH_EDITOR
	const ULuaEditorSetting * LuaSetting = GetDefault<ULuaEditorSetting>();
	if(LuaSetting && !LuaSetting->LuaSourceRootDirInEditor.Path.IsEmpty())
	{
		ResultFilePath = FPaths::ConvertRelativePathToFull(LuaSetting->LuaSourceRootDirInEditor.Path);
	}
	else
#endif
	{
		ResultFilePath = FPaths::GameContentDir() / TEXT("LuaSource/");
	}
	
#endif 
#if PLATFORM_ANDROID
	ResultFilePath = (GFilePathBase + FString(FILEBASE_DIRECTORY) + FApp::GetProjectName()) / FApp::GetProjectName() / TEXT("Saved/LuaSource");
#endif 

#if PLATFORM_IOS
	ResultFilePath = FString(FPaths::ProjectSavedDir()) / TEXT("LuaSource");
#endif

	return FPaths::ConvertRelativePathToFull(ResultFilePath);
}

bool FLuaSrcFile::Initialize(NS_SLUA::lua_State * inL)
{
#if PLATFORM_WINDOWS
	const char * base_dir = TCHAR_TO_UTF8(*BaseDir());
	NS_SLUA::LuaObject::push(inL,base_dir);
	NS_SLUA::lua_setglobal(inL,"_luadir");
#endif
	return true;
}


bool FLuaSrcFile::LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath)
{
	InFilePath = MakeAbsFilePath(FString(fn));
	
	{
		IPlatformFile & PlatformFile = IPlatformFile::GetPlatformPhysical();
		IFileHandle* Handle = PlatformFile.OpenRead( *InFilePath);
		if(!Handle)
		{
			return false;
		}
		int64 TotalSize = Handle->Size();
		Handle->Seek(0);
		// Allocate slightly larger than file size to avoid re-allocation when caller null terminates file buffer
		OutContent.Reset( TotalSize );
		OutContent.AddUninitialized( TotalSize );
		Handle->Read(OutContent.GetData(), TotalSize);
		Handle->Flush();
		delete Handle;
		Handle = nullptr;
	}
	
	if (OutContent.Num() > 0) {
		return true;
	}

	return false;
}

FString FLuaSrcFile::MakeAbsFilePath(FString const & InFilePath)
{
	FString LuaFilePath = InFilePath;
	FString SrcFilePath = BaseDir();
	if (LuaFilePath.EndsWith(TEXT(".lua")))
	{
		LuaFilePath.RemoveAt(LuaFilePath.Len() - 4);
	}
	LuaFilePath = SrcFilePath / InFilePath.Replace(TEXT("."), TEXT("/")) + TEXT(".lua");
	if (IsExists(LuaFilePath))
	{
		return LuaFilePath;
	}
	else
	{
		LuaFilePath = SrcFilePath / TEXT("Debug") / InFilePath.Replace(TEXT("."), TEXT("/")) + TEXT(".lua");
		if (IsExists(LuaFilePath))
		{
			return LuaFilePath;
		}
	}
	UE_LOG(LuaFile, Warning, TEXT("MakeAbsFilePath %s Failer"), *InFilePath);

	return TEXT("");
}

bool FLuaSrcFile::IsExists(FString const & InFilePath)
{
	IPlatformFile & PlatformFile = IPlatformFile::GetPlatformPhysical();
	
	return PlatformFile.FileExists(*InFilePath);
}

bool FLuaSrcFile::IsEnable()
{
#if WITH_EDITOR
	return true;
#endif

#if PLATFORM_ANDROID || PLATFORM_IOS
	FString LuaMainFilePath = MakeAbsFilePath(TEXT("main"));
	if (IsExists(LuaMainFilePath))
	{
		return true;
	}
#endif
	// Debug LUA Switch
	if (FParse::Param(FCommandLine::Get(), TEXT("DLua")))
	{
		return true;
	}
	return false;
}

//////////////////////////////////////////////////////////////////////////

FLuaPakFile::~FLuaPakFile()
{

}

bool FLuaPakFile::Initialize(NS_SLUA::lua_State * inL)
{
	return true;
}

bool FLuaPakFile::LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath)
{
	FString LuaFilePath = MakeLuaObjPath(fn);
	if(IsExists(LuaFilePath))
	{
		FFileHelper::LoadFileToArray(OutContent, *LuaFilePath);
		if (OutContent.Num() > 0) 
		{
			InFilePath = LuaFilePath;
			return true;
		}
	}
	UE_LOG(LuaFile,Log,TEXT("load File Content Error %s"),*LuaFilePath);
	return false;
}

bool FLuaPakFile::IsExists(FString const & InFilePath)
{
	bool is_exists = IFileManager::Get().FileExists(*InFilePath);
	if(!is_exists)
	{
		UE_LOG(LuaFile,Log,TEXT("Lua File %s not exists"),*InFilePath);
	}
	return is_exists;
}

FString FLuaPakFile::MakeLuaObjPath(FString const & InFilePath)
{
	FString LuaFilePath = InFilePath;
	LuaFilePath.RemoveFromEnd(TEXT(".lua"));
	LuaFilePath = LuaFilePath.Replace(TEXT("."), TEXT("/"));
	LuaFilePath = TEXT("../../../NZM/Content/LuaSource") / LuaFilePath.Append(TEXT(".lua"));
	return LuaFilePath;
}


bool FLuaPakFile::IsEnable()
{
	return true;
}

