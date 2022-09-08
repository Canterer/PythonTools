// Copyright 2020 Tencent Inc.  All rights reserved.
//
// Author: ruiqingkong@tencent.com
//
// Lua游戏配置
// ...

#pragma once
#include "CoreMinimal.h"
#include "LuaSetting.generated.h"
UCLASS(Config = Game, defaultconfig)
class LUARUNTIME_API ULuaSetting : public UObject
{
	GENERATED_BODY()
public:
	UPROPERTY(config, EditAnywhere, Category = "LuaSetting",meta = (AllowClass = "World"))
	FSoftObjectPath StartupMap;
	UPROPERTY(config, EditAnywhere, Category = "LuaSetting", meta = (AllowClass = "World"))
	TArray<FSoftObjectPath> EnableLuaMap;

	UPROPERTY(Config,EditAnywhere,Category="LuaSetting")
	FString GameStartupScript;

};

UCLASS(Config = Game, globaluserconfig)
class LUARUNTIME_API ULuaEditorSetting : public UObject
{
	GENERATED_BODY()
public:
	UPROPERTY(config, EditAnywhere, Category = "Editor")
	FDirectoryPath LuaSourceRootDirInEditor;
	UPROPERTY(config, EditAnywhere, Category = "Editor")
	FFilePath FileEditorLocation;
};
