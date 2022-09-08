// Copyright 2020 Tencent Inc.  All rights reserved.
//
// Author: ruiqingkong@tencent.com
//
// Lua代码验证逻辑
// ...

#pragma once

#include "CoreMinimal.h"
#include "UObject/ObjectMacros.h"
#include "Commandlets/Commandlet.h"
#include "ValidLuaCommandlet.generated.h"

UCLASS()
class UValidLuaCommandlet : public UCommandlet
{
	GENERATED_BODY()

	//~ Begin UCommandlet Interface
	virtual int32 Main(const FString& CmdLineParams) override;
	//~ End UCommandlet Interface
	
private:
	FString MapPackageName;
private:
	FString Params;
	/** All commandline tokens */
	TArray<FString> Tokens;
	/** All commandline switches */
	TArray<FString> Switches;
};


