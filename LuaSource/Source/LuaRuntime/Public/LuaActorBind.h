// Copyright 2020 Tencent Inc.  All rights reserved.
//
// Author: ruiqingkong@tencent.com
//
// Lua绑定Actor的类
// ...
#pragma once
#include "CoreMinimal.h"

#include "LuaFileTag.h"
#include "Components/ActorComponent.h"
#include "LuaActorBind.generated.h"
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class LUARUNTIME_API ULuaActorBindComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
public:
	UPROPERTY(EditAnywhere)
	FLuaFileTag LuaFileTag;
	
};
