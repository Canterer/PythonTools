// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "LuaBlueprintLibrary.h"
#include "LuaBlueprintBridge.generated.h"

UENUM()
namespace ELuaArgumentType
{
	enum Type
	{
		None = 0,
		Boolean,
		Int,
		Float,
		String,
		Object,
		// Add new enum types at the end only! They are serialized by index.
	};
}

UCLASS()
class LUARUNTIME_API ULuaBlueprintBridge : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:

	UFUNCTION(BlueprintCallable)
	static void LuaCallFunction(UObject* WorldContextObject, FString funcname,const TArray<FLuaBPVar>& args,FString StateName);
	UFUNCTION(BlueprintPure)
	static FLuaBPVar CreateVarFromObject(UObject* WorldContextObject, UObject* InTheObject); 
};
