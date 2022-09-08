#pragma once

#include "Modules/ModuleManager.h"
#include "LuaState.h"
#include "LuaStateHelper.h"
class FLuaTimerManager;
class FLuaFileManager;


class LUARUNTIME_API FLuaRuntime : public FDefaultGameModuleImpl
{
public:
	FLuaRuntime();
	virtual void StartupModule();
	virtual void ShutdownModule();

	static FLuaRuntime & Get();

	template<class...Args>
	static void CallGlobal(const char* func, Args...args)
	{
// 		NS_SLUA::lua_State* inL = FNZLuaRuntime::GetLuaStateWithName(TEXT("frontend"));
// 		USING_NAMESPACE_NS_SLUA
// 		NS_SLUA::lua_getglobal(inL, func);
// 		if (NS_SLUA::lua_type(inL, -1) == LUA_TFUNCTION)
// 		{
// 			FLuaStateHelper::PushAll(inL, args...);
// 			const int32 ParamCount = sizeof...(args);
// 			lua_call(inL, ParamCount, 0);
// 		}
// 		else
// 		{
// 			NS_SLUA::lua_pop(inL, 1);
// 		}
	}
public:
	bool LoadLuaFile(const char* fn, TArray<uint8>& OutContent, FString& filepath);
#if WITH_EDITOR
	bool LoadLuaFileInEditor(const char* fn, TArray<uint8>& OutContent, FString& filepath);
#endif
private:
	void OnLuaStateInited(NS_SLUA::lua_State * inL);
	void OnLuaStateClose(NS_SLUA::lua_State * inL);

	void OnPostLoadMap(UWorld * InWorld);
	void OnWorldCleanup(UWorld * InWorld,bool,bool);
private:
	TSharedPtr<class FLuaFileManager> LuaFileManager;
	
};
