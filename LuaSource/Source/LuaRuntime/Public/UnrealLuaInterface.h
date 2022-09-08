// Copyright 2020 Tencent Inc.  All rights reserved.
//
// Author: ruiqingkong@tencent.com
//
// Lua访问总控接口
// ...
#pragma once
#include "slua.h"
#include "LuaBind.h"
#include "LuaCppBinding.h"
#include "Unrealluainterface.generated.h"
class UGameInstance;

UCLASS()
class LUARUNTIME_API UUnrealLuaInterface : public UBlueprintFunctionLibrary
{
public:
	GENERATED_BODY()
public:
	UFUNCTION()
	static int32 RunLuaCode(UObject * LuaWorld,FString const & InLuaCode);
};
