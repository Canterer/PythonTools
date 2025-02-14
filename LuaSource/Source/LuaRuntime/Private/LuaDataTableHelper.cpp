// Fill out your copyright notice in the Description page of Project Settings.

#include "LuaDataTableHelper.h"

#include "UserDefineClassMacro.h"
DataTableForLua::DataTableForLua(NS_SLUA::lua_State* inL, UDataTable* _Data) :Data(_Data)
{
	if (Data)
	{
// 		if (UUserDefinedStruct* BpStruct = Cast<UUserDefinedStruct>(Data->RowStruct))
// 		{
// 			RowStructTypeName = BpStruct->GetName();
// 		}
// 		else
// 			RowStructTypeName = "F" + Data->RowStruct->GetName();

		RowStructTypeName = Data->RowStruct->GetName();
	}
}


void DataTableForLua::AddReferencedObjects( FReferenceCollector& Collector )
{
	if (Data != nullptr)
	{
		Collector.AddReferencedObject(Data);
	}
}

int32 DataTableForLua::Destroy(NS_SLUA::lua_State* inL)
{
	DataTableForLua* Self = NS_SLUA::LuaObject::checkUD<DataTableForLua>(inL, 1);
	if (Self)
	{
		Self->Data = nullptr;
		delete Self;
	}

	return 0;
}

int32 DataTableForLua::FindRow(NS_SLUA::lua_State * inL)
{

	FName Key = FName(UTF8_TO_TCHAR(NS_SLUA::LuaObject::checkValue<const char*>(inL, 2)));
	if (Data && Data->GetRowMap().Contains(Key))
	{
		uint8* RowPtr = (Data->GetRowMap())[Key];

		uint32 size = Data->RowStruct ? Data->RowStruct->GetStructureSize() : 1;
		uint8* buf = (uint8*)FMemory::Malloc(size);
		Data->RowStruct->InitializeStruct(buf);
		Data->RowStruct->CopyScriptStruct(buf, RowPtr);

		NS_SLUA::LuaStruct* pStruct = new NS_SLUA::LuaStruct(buf, size, Data->RowStruct);
		NS_SLUA::LuaObject::push(inL, pStruct );
		return 1;
	}
	return 0;
}

int32 DataTableForLua::GetAllRows(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	NS_SLUA::lua_newtable(inL);

	TMap<FName, uint8*> AllRowMap = Data->GetRowMap();
	for (auto& ThePair : AllRowMap)
	{
		NS_SLUA::LuaObject::push(inL, ThePair.Key);
		uint8* RowPtr = ThePair.Value;

		uint32 size = Data->RowStruct ? Data->RowStruct->GetStructureSize() : 1;
		uint8* buf = (uint8*)FMemory::Malloc(size);
		Data->RowStruct->InitializeStruct(buf);
		Data->RowStruct->CopyScriptStruct(buf, RowPtr);

		NS_SLUA::LuaStruct* pStruct = new NS_SLUA::LuaStruct(buf, size, Data->RowStruct);
		NS_SLUA::LuaObject::push(inL, pStruct );
		NS_SLUA::lua_rawset(inL, -3);
	}

	return AllRowMap.Num() > 0 ? 1 : 0;
}

TArray<FName> DataTableForLua::GetRowNames() const
{
	return Data->GetRowNames();
}

int32 DataTableForLua::Table(NS_SLUA::lua_State* inL)
{
	
	NS_SLUA::lua_newtable(inL);
	for (auto& ThePair : Data->GetRowMap())
	{
		NS_SLUA::LuaObject::push(inL, ThePair.Key);
		uint8* RowPtr = ThePair.Value;
		
		uint32 size = Data->RowStruct ? Data->RowStruct->GetStructureSize() : 1;
		uint8* buf = (uint8*)FMemory::Malloc(size);
		Data->RowStruct->InitializeStruct(buf);
		Data->RowStruct->CopyScriptStruct(buf, RowPtr);

		NS_SLUA::LuaStruct * pStruct = new NS_SLUA::LuaStruct(buf, size, Data->RowStruct);

		NS_SLUA::LuaObject::push(inL,pStruct);
		NS_SLUA::lua_rawset(inL, -3);
	}
	return 1;
}

int FLuaDataTableHelper::GetDataTable(NS_SLUA::lua_State*inL)
{
	FString TableName = UTF8_TO_TCHAR(NS_SLUA::LuaObject::checkValue<const char*>(inL, 1));
	FString path = TableName;
	if(!TableName.StartsWith(TEXT("/Game/")))
	{
		path = FString::Printf(TEXT("/Game/DataTables/%s"), *TableName);
	}

	UDataTable* CurDataTable = LoadObject<UDataTable>(NULL, *path);
	if (CurDataTable == nullptr)
	{
		UE_LOG(LogTemp, Log, TEXT("Lua GetDataTable Failed! TablePath = %s"), *path);
		ensureAlwaysMsgf(0, TEXT("Bug"));
		return 0;
	}
	DataTableForLua* LuaData = new DataTableForLua(inL, CurDataTable);
	NS_SLUA::LuaObject::pushType(inL, LuaData, "DataTableForLua",nullptr,nullptr);
	return 1;
}

int FLuaDataTableHelper::SeializeToTable(NS_SLUA::lua_State*inL,UDataTable * InDataTable)
{
	if(!InDataTable)
	{
		return 0;
	}
	if(InDataTable->RowStruct == nullptr)
	{
		return 0;
	}
	NS_SLUA::lua_createtable(inL,1,1); // t
	
	NS_SLUA::LuaObject::push(inL,"RowStruct"); // t "RowStruct"
	

	// table.pack
	NS_SLUA::lua_getglobal(inL,"table");
	NS_SLUA::lua_pushstring(inL,"pack");
	NS_SLUA::lua_rawget(inL,-2);
	lua_remove(inL,-2);  // t "RowStruct" func(table.pack)
	int32 nPropertyNum = 0;
	TArray<UProperty *> DataTableColPropertys;
	for (TFieldIterator<UProperty> It(InDataTable->RowStruct); It; ++It)
	{
		UProperty* Prop = *It;
		FString PropName = Prop->GetAuthoredName();
		NS_SLUA::LuaObject::push(inL,PropName); // t "RowStruct" func(table.pack) param...
		DataTableColPropertys.Add(Prop);
		nPropertyNum += 1;
	}

	if(nPropertyNum > 0)
	{
		lua_call(inL,nPropertyNum,1); // t "RowStruct" result(table.pack)

		NS_SLUA::lua_rawset(inL,-3); // t
	}
	else
	{
		lua_pop(inL,2);
 	}
	// t 
	NS_SLUA::lua_pushstring(inL,"RowArray"); // t "RowStruct"


	TMap<FName, uint8*> const & RowMap = InDataTable->GetRowMap();

	// table.pack
	NS_SLUA::lua_getglobal(inL, "table");
	NS_SLUA::lua_pushstring(inL, "pack");
	NS_SLUA::lua_rawget(inL, -2);
	lua_remove(inL, -2);  // t "RowStruct" func(table.pack)
	int32 table_pack_absindex = NS_SLUA::lua_absindex(inL,-1);
	int32 nRowNum = 0;
	for(TPair<FName,uint8 *> const & Item : RowMap)
	{
		//
		NS_SLUA::lua_pushvalue(inL,table_pack_absindex);
		for(int32 i = 0; i < nPropertyNum; ++ i)
		{
			UProperty * Prop = DataTableColPropertys[i];
			check(Prop);
			if(NS_SLUA::LuaObject::getPusher(Prop))
			{
				NS_SLUA::LuaObject::push(inL,Prop,Item.Value);
			}
			else
			{
				// TODO:
			}
		}
		lua_call(inL,nPropertyNum,1);
		nRowNum += 1;
	}

	if(nRowNum > 0)
	{
		lua_call(inL, nRowNum, 1); // t "RowStruct" result(table.pack)

		NS_SLUA::lua_rawset(inL, -3); // t
	}
	else
	{
		lua_pop(inL,2);
	}
	return 1;
}
	
NAMESPACE_NS_SLUA_BEGIN
	LUA_GLUE_BEGIN(DataTableForLua)
	LUA_GLUE_FUNCTION(Table)
	LUA_GLUE_FUNCTION(FindRow)
	LUA_GLUE_GC(Destroy)
	LUA_GLUE_END()

	DefLuaClass(FLuaDataTableHelper)
	DefLuaMethod(GetDataTable, &FLuaDataTableHelper::GetDataTable)
	EndDef(FLuaDataTableHelper, nullptr)
NAMESPACE_NS_SLUA_END
