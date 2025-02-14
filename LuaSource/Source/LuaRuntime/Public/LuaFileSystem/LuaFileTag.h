#pragma once
#include "LuaFileTag.generated.h"

USTRUCT(BlueprintType)
struct LUARUNTIME_API FLuaFileTag
{
	GENERATED_USTRUCT_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString LuaFilePath;

	FString ToString() const
	{
		return LuaFilePath;
	}

	bool IsEmpty() const
	{
		return LuaFilePath.IsEmpty();
	}
};
