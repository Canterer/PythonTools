// Fill out your copyright notice in the Description page of Project Settings.

#pragma once
#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "UObject/GCObject.h"
#include "Engine/DataTable.h"
#include "slua.h"
#include "LuaCppBinding.h"

#include "Engine/UserDefinedStruct.h"

class DataTableForLua : public FGCObject
{
public:
	DataTableForLua(NS_SLUA::lua_State*inL, UDataTable* _Data);
	void AddReferencedObjects( FReferenceCollector& Collector );
	static int32 Destroy(NS_SLUA::lua_State* inL);
	int32 FindRow(NS_SLUA::lua_State * inL);
	int32 GetAllRows(NS_SLUA::lua_State* inL);
	int32 Table(NS_SLUA::lua_State* inL);
	TArray<FName> GetRowNames() const;
private:
	FString RowStructTypeName;
	UDataTable * Data;
};


class FLuaDataTableHelper 
{
public: 
	static int GetDataTable(NS_SLUA::lua_State*inL);
	static int SeializeToTable(NS_SLUA::lua_State*inL,UDataTable * InDataTable);
};
