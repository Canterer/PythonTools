// Copyright 2020 Tencent Inc.  All rights reserved.
//
// Author: ruiqingkong@tencent.com
//
// LuaSubsystem 全局单例,负责全局state的初始化
// ...
#pragma once
#include "Subsystems/GameInstanceSubsystem.h"
#include "slua.h"
#include "LuaTimer.h"
#include "LuaSubSystem.generated.h"


struct FLuaGameWorldWrapper
{
	int32 LuaThreadRef;
	NS_SLUA::lua_State * TheState = nullptr;
	TWeakObjectPtr<UWorld> GameWorld;
};

class FLuaStateWrapper
{
public:
	FLuaStateWrapper(const char* InStateName);
	bool IsValid = false;
	NS_SLUA::LuaState TheSLuaState;
	
	TWeakObjectPtr<UGameInstance> GameIns;
	TArray<FLuaGameWorldWrapper> GameWorldToLuaThread;
	int32 WorldRef = -1;
	TSharedPtr<FLuaTimerManager> TimerManager;
};

DECLARE_MULTICAST_DELEGATE_OneParam(FOnLuaStateDelegate, NS_SLUA::lua_State*);

UCLASS()
class LUARUNTIME_VTABLE ULuaSubSystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	void Initialize(FSubsystemCollectionBase& Collection) override;
	void Deinitialize() override;

	static LUARUNTIME_API int32 GetCacheBindRef(const UGameInstance * WorldContext);
	static LUARUNTIME_API NS_SLUA::lua_State * GetThreadLuaState(const UObject * InWorldContext);
	static LUARUNTIME_API void StartupLua(UObject * InWorldContext,FString const & InStartupLuaFilePath);

	static LUARUNTIME_API FOnLuaStateDelegate OnLuaStateInitCallback;
	static LUARUNTIME_API FOnLuaStateDelegate OnLuaStateCloseCallback;

	void CreateLuaWorld(UWorld* InWorld);
	void DestroyLuaWorld(UWorld * InWorld);

	
private:
	void StartupLua(FString const & InStartupLuaFilePath);
	void LuaStateInitCallback();
	void SetupGlobalVariable();
private:
	TSharedPtr<FLuaStateWrapper> MainStateWrapper;
	
};
