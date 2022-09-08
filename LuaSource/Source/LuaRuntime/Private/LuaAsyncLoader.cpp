#include "LuaAsyncLoader.h"
#include "UserDefineClassMacro.h"
#include "NZAssetManager.h"

namespace LuaAsyncLoader
{
USING_NAMESPACE_NS_SLUA

static int32 _index = 0;
static TMap<int32, TSharedPtr<FStreamableHandle>> _Handles;

int32 RequestAsyncLoad(lua_State* inL)
{
	UObject* RequestObject = LuaObject::checkValue<UObject*>(inL, 1);
	const char* buf = LuaObject::checkValue<const char*>(inL, 2);
	LuaVar LuaFunc(inL, 3);
	if(!LuaFunc.isFunction())
	{
		return 0;	
	}
	const TAsyncLoadPriority Prioprity = LuaObject::checkValue<TAsyncLoadPriority>(inL, 4);
	
	FSoftObjectPath AssetRef(buf);
	
	FStreamableDelegate Delegate;
	Delegate.BindLambda([LuaFunc, AssetRef]()
	{
		UObject* obj = AssetRef.ResolveObject();
		if (!obj)
		{
			LuaFunc.call();
		}
		else if (obj->IsA(UBlueprintGeneratedClass::StaticClass()))
		{
			LuaFunc.call(Cast<UBlueprintGeneratedClass>(obj));
		}
		else if (obj->IsA(UClass::StaticClass()))
		{
			LuaFunc.call(Cast<UClass>(obj));
		}
		else if (obj->IsA(UBlueprintCore::StaticClass()))
		{
			UBlueprintCore* bp_obj = Cast<UBlueprintCore>(obj);
			if (bp_obj)
			{
				LuaFunc.call(bp_obj->GeneratedClass.Get());
			}
		}
		else
		{
			LuaFunc.call(AssetRef.ResolveObject());
		}
	});
	TSharedPtr<FStreamableHandle> Handle = UNZAssetManager::Get().NZRequestAsyncLoad(RequestObject, AssetRef, Delegate, Prioprity);
	_Handles.Add(++_index, Handle);
	return LuaObject::push(inL, _index);
}

int32 CancelAsyncLoad(lua_State* inL)
{
	int32 Index = LuaObject::checkValue<int32>(inL, 1);
	if(TSharedPtr<FStreamableHandle>* Handler = _Handles.Find(Index))
	{
		UNZAssetManager::Get().NZReleaseStreamableHandle(*Handler);	
		_Handles.Remove(Index);
	}
	return 0;
}

void Open(lua_State* inL)
{
	lua_newtable(inL);

	luaL_Reg all_functions [] = {
		{"RequestAsyncLoad",&RequestAsyncLoad},
		{"CancelAsyncLoad",&CancelAsyncLoad},
		{NULL,NULL}
	};
	luaL_setfuncs(inL,all_functions,0);

	lua_setglobal(inL,"FLuaAsyncLoader");
}
}
