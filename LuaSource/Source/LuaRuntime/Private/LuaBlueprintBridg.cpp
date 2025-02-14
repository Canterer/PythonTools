// Fill out your copyright notice in the Description page of Project Settings.

#include "LuaBlueprintBridge.h"
#include "slua.h"

void ULuaBlueprintBridge::LuaCallFunction(UObject* WorldContextObject, FString funcname,const TArray<FLuaBPVar>& args,FString StateName)
{
	USING_NAMESPACE_NS_SLUA
	if(WorldContextObject == nullptr)
	{
		return;
	}
	if(!WorldContextObject->GetWorld())
	{
		return;
	}
	UWorld * ThisWorld = WorldContextObject->GetWorld();

	auto ls = LuaState::get(ThisWorld->GetGameInstance());
	if (StateName.Len() != 0) ls = LuaState::get(StateName);
	if (!ls)
	{
		return;
	}
	if(ILuaTableObjectInterface * Interface = (ILuaTableObjectInterface *)WorldContextObject->GetInterfaceAddress(ULuaTableObjectInterface::StaticClass()))
	{
		LuaVar selfTable = Interface->getSelfTable();
		if(selfTable.isValid() && selfTable.isTable())
		{
			//selfTable.push(ls->getLuaState());
			LuaVar lfunc = selfTable.getFromTable<NS_SLUA::LuaVar,const char *>(TCHAR_TO_UTF8(*funcname), true);
			if(lfunc.isFunction())
			{
				selfTable.push(ls->getLuaState());
				for (auto& arg : args) {
					arg.value.push(ls->getLuaState());
				}
				//
				lfunc.callWithNArg(args.Num() + 1);
				return;
			}
		}
	}
	//

	LuaVar f = ls->get(TCHAR_TO_UTF8(*funcname));
	if (!f.isFunction()) {
		Log::Error("Can't find lua member function named %s to call", TCHAR_TO_UTF8(*funcname));
		return;
	}

	for (auto& arg : args) {
		arg.value.push(ls->getLuaState());
	}
	f.callWithNArg(args.Num());
}

FLuaBPVar ULuaBlueprintBridge::CreateVarFromObject(UObject* WorldContextObject, UObject* InTheObject)
{
	USING_NAMESPACE_NS_SLUA
	if(WorldContextObject == nullptr)
	{
		return FLuaBPVar();
	}
	UWorld * TheWorld = WorldContextObject->GetWorld();
	if(!TheWorld)
	{
		return FLuaBPVar();
	}
	auto ls = LuaState::get(TheWorld->GetGameInstance());
	if (!ls) return FLuaBPVar();

	LuaObject::push(ls->getLuaState(), InTheObject);
	LuaVar ret(ls->getLuaState(), -1);
	lua_pop(ls->getLuaState(), 1);
	return FLuaBPVar(ret);
}
