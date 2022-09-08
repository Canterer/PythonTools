#pragma once
#include "LuaState.h"
#include "LuaVar.h"
#include "GameFramework/GameModeBase.h"

#include <luaconf.h>

class UGameInstance;

class FGPLuaGameplay
{
public:
	static FGPLuaGameplay& Get()
	{
		static  FGPLuaGameplay LuaGameplay;
		return LuaGameplay;
	}
	
	void OnLuaSubSystemDeinitialize();

	void OnLuaStateInit(NS_SLUA::lua_State * inL);
	void OnLuaStateClose(NS_SLUA::lua_State * inL);
	
	void OnEngineTick() const;
	void OnGameModeCreated(AGameModeBase* GameMode);
	
private:
	void OnLuaSubSystemInitialize(const UGameInstance * GameInstance);
	
	static int BindObject(NS_SLUA::lua_State* L);
	static int UnBindObject(NS_SLUA::lua_State* L);
	static int RegisterComponent(NS_SLUA::lua_State* L);
	static int UnRegisterComponent(NS_SLUA::lua_State* L);
	
	static int __indexCppInstance(NS_SLUA::lua_State* L);
	static int __newindexCppInstance(NS_SLUA::lua_State* L);
	static int __trySetCppInstance(NS_SLUA::lua_State* L);
	static void _bindOverrideFunc(NS_SLUA::LuaVar luaTable,UObject * obj);
	
	#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
	static void hookBpScript(UFunction* func, FNativeFuncPtr hookfunc);
	#else
	static void hookBpScript(UFunction * func, Native hookfunc);
	#endif

private:
	NS_SLUA::lua_State* cur_lua_state = nullptr;

	NS_SLUA::LuaVar InitTable;
	NS_SLUA::LuaVar TickFunc;
};

class UtilsFuncs
{
public:
	
};
