#include "LuaRuntimeModule.h"
#include "CoreMinimal.h"
#include "UserDefineClassMacro.h"
#include "LuaTimer.h"
#include "Engine/World.h"
#include "LuaSubsystem.h"
#include "LuaFileSystem/LuaFileManager.h"

static TArray<uint8> LoadLuaFile_Func(const char* fn, FString& filepath)
{
	static FLuaRuntime& Module = FModuleManager::Get().GetModuleChecked<FLuaRuntime>("LuaRuntime");
	TArray<uint8> OutContent;
	if (Module.LoadLuaFile(fn, OutContent, filepath))
	{
		//TODO.. Log
	}

	return OutContent;
}

FLuaRuntime::FLuaRuntime()
{
}

FLuaRuntime & FLuaRuntime::Get()
{
	FLuaRuntime & Module = FModuleManager::Get().GetModuleChecked<FLuaRuntime>("LuaRuntime");
	return Module;
}

void FLuaRuntime::StartupModule()
{
	ULuaSubSystem::OnLuaStateInitCallback.AddRaw(this,&FLuaRuntime::OnLuaStateInited);
	ULuaSubSystem::OnLuaStateCloseCallback.AddRaw(this,&FLuaRuntime::OnLuaStateClose);


	FCoreUObjectDelegates::PostLoadMapWithWorld.AddRaw(this, &FLuaRuntime::OnPostLoadMap);
	FWorldDelegates::OnWorldCleanup.AddRaw(this, &FLuaRuntime::OnWorldCleanup);
	
}

void FLuaRuntime::ShutdownModule()
{
	if(LuaFileManager.IsValid())
	{
		LuaFileManager.Reset();
	}
	ULuaSubSystem::OnLuaStateInitCallback.RemoveAll(this);
	ULuaSubSystem::OnLuaStateCloseCallback.RemoveAll(this);
}

void FLuaRuntime::OnLuaStateInited(NS_SLUA::lua_State * inL)
{
	if(inL)
	{
		if(!LuaFileManager.IsValid())
		{
			LuaFileManager = MakeShareable(new FLuaFileManager());
		}
		LuaFileManager->Init(inL);

		NS_SLUA::LuaState * TheLuaState = NS_SLUA::LuaState::get(inL);
		if(TheLuaState)
		{
			TheLuaState->setLoadFileDelegate(LoadLuaFile_Func);
		}
	}
}

void FLuaRuntime::OnLuaStateClose(NS_SLUA::lua_State * inL)
{
	NS_SLUA::LuaState* TheLuaState = NS_SLUA::LuaState::get(inL);
	if (TheLuaState)
	{
		TheLuaState->setLoadFileDelegate(nullptr);
	}
}

void FLuaRuntime::OnPostLoadMap(UWorld* InWorld)
{
	if(InWorld  && InWorld->GetGameInstance())
	{
		ULuaSubSystem * LuaSubsystem = InWorld->GetGameInstance()->GetSubsystem<ULuaSubSystem>();

		if(LuaSubsystem)
		{
			LuaSubsystem->CreateLuaWorld(InWorld);
		}
		
	}
}

void FLuaRuntime::OnWorldCleanup(UWorld* InWorld,bool,bool)
{
	if(InWorld  && InWorld->GetGameInstance())
	{
		ULuaSubSystem * LuaSubsystem = InWorld->GetGameInstance()->GetSubsystem<ULuaSubSystem>();

		if(LuaSubsystem)
		{
			LuaSubsystem->DestroyLuaWorld(InWorld);
		}
		
	}
}

bool FLuaRuntime::LoadLuaFile(const char* fn, TArray<uint8>& OutContent, FString& filepath)
{
	if (LuaFileManager.IsValid())
	{
		return LuaFileManager->LoadFileContent(fn, OutContent, filepath);
	}

	return false;
}
#if WITH_EDITOR
bool FLuaRuntime::LoadLuaFileInEditor(const char* fn, TArray<uint8>& OutContent, FString& filepath)
{
	if (!LuaFileManager.IsValid())
	{
		LuaFileManager = MakeShareable(new FLuaFileManager());
		LuaFileManager->Init(nullptr);
	}
	return LoadLuaFile(fn,OutContent,filepath);
}

#endif

IMPLEMENT_MODULE(FLuaRuntime,LuaRuntime)

