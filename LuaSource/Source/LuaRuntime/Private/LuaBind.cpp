#include "LuaBind.h"
#include "CoreMinimal.h"

#include <lua.h>


#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
extern uint8 GRegisterNative(int32 NativeBytecodeIndex, const FNativeFuncPtr& Func);
#else
extern uint8 GRegisterNative(int32 NativeBytecodeIndex, const Native& Func);
#endif
#define Ex_LuaHook (EX_Max-1)

static int setParent(NS_SLUA::lua_State* L) {
	// set field to obj, may raise an error
	lua_settable(L, 1);
	return 0;
}


int FLuaBindBridge::__index(NS_SLUA::lua_State* L)
{
	USING_NAMESPACE_NS_SLUA
	lua_pushstring(L, SLUA_CPPINST);
	lua_rawget(L, 1);
	void* ud = lua_touserdata(L, -1);
	if (!ud)
		luaL_error(L, "expect LuaBase table at arg 1");
	lua_pop(L, 1);
	UObject* obj = (UObject*)ud;
	if (!NS_SLUA::LuaObject::isUObjectValid(obj))
	{
		return 0;
	}
	LuaObject::push(L, obj, true);

	// push key
	lua_pushvalue(L, 2);
	// get field from real actor
	lua_gettable(L, -2);
	return 1;
}

int FLuaBindBridge::__newindex(NS_SLUA::lua_State* L)
{
	USING_NAMESPACE_NS_SLUA
	lua_pushstring(L, SLUA_CPPINST);
	lua_rawget(L, 1);
	void* ud = lua_touserdata(L, -1);
	if (!ud)
		luaL_error(L, "expect LuaBase table at arg 1");
	lua_pop(L, 1);
	LuaObject::push(L, (UObject*)ud, false);

	lua_pushcfunction(L, setParent);
	// push cpp inst
	lua_pushvalue(L, -2);
	// push key
	lua_pushvalue(L, 2);
	// push value
	lua_pushvalue(L, 3);
	// set ok?
	if (lua_pcall(L, 3, 0, 0)) {
		lua_pop(L, 1);
		// push key
		lua_pushvalue(L, 2);
		// push value
		lua_pushvalue(L, 3);
		// rawset to table
		lua_rawset(L, 1);
	}
	return 0;
}

void FLuaBindBridge::bindOverrideFunc(NS_SLUA::lua_State * inL,int32 const TableIndex,UObject * obj)
{
	ensure(obj && inL);
	UClass* cls = obj->GetClass();
	ensure(cls);
	
	EFunctionFlags availableFlag = FUNC_BlueprintEvent;
	for (TFieldIterator<UFunction> it(cls); it; ++it) {
		if (!(it->FunctionFlags & availableFlag))
			continue;
		NS_SLUA::lua_pushstring(inL,TCHAR_TO_UTF8(*it->GetName()));
		NS_SLUA::lua_rawget(inL,TableIndex);
		if(lua_isfunction(inL,-1))
		{
			#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
			hookBpScript(*it, (FNativeFuncPtr)&luaOverrideFunc);
			#else
			hookBpScript(*it, (Native)&LuaBase::luaOverrideFunc);
			#endif
		}
		lua_pop(inL,1);
	}
}

#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
DEFINE_FUNCTION(FLuaBindBridge::luaOverrideFunc)
#else
void FLuaBindBridge::luaOverrideFunc(FFrame& Stack, RESULT_DECL)
#endif
{
	USING_NAMESPACE_NS_SLUA
	UFunction* func = Stack.Node;
	ensure(func);
	UObject* lb = Stack.Object;//checkBase(Stack.Object);

	// maybe lb is nullptr, some member function with same name in different class
	// we don't care about it
	if (!lb) {
		*(bool*)RESULT_PARAM = false;
		return;
	}

	ensure(lb);

	// if (lb->indexFlag == LuaBase::IF_RPC && lb->currentFunction == func) {
	// 	*(bool*)RESULT_PARAM = false;
	// 	return;
	// }

	void* params = Stack.Locals;

	UGameInstance * GameIns = getGameInstance(lb);
	if(!GameIns) return;
	NS_SLUA::LuaState* ls = NS_SLUA::LuaState::get(GameIns);
	if (!ls) return ;
	lua_State * L = ls->getLuaState();
	int32 BindRef = ULuaSubSystem::GetCacheBindRef(GameIns);
	if(BindRef != LUA_NOREF)
	{
		lua_rawgeti(L,LUA_REGISTRYINDEX,BindRef);
		lua_rawgetp(L,-1,lb);
		if(lua_istable(L,-1))
		{
			NS_SLUA::LuaVar luaSelfTable(L,-1,LuaVar::Type::LV_TABLE);
			lua_pushstring(L,TCHAR_TO_UTF8(*func->GetName()));
			if(lua_isfunction(L,-1))
			{
				NS_SLUA::LuaVar lfunc(L,1,LuaVar::Type::LV_FUNCTION);
				lfunc.callByUFunction(func, (uint8*)params, Stack.OutParms, nullptr, &luaSelfTable);
				*(bool*)RESULT_PARAM = true;
			}
		}
	}

	*(bool*)RESULT_PARAM = false;
}


#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
void FLuaBindBridge::hookBpScript(UFunction* func, FNativeFuncPtr hookfunc) {
#else
void FLuaBindBridge::hookBpScript(UFunction * func, Native hookfunc) {
#endif
	static bool regExCode = false;
	if (!regExCode) {
		GRegisterNative(Ex_LuaHook, hookfunc);
		regExCode = true;
	}
	// if func had hooked
	if (func->Script.Num() > 5 && func->Script[5] == Ex_LuaHook)
		return;
	// if script isn't empty
	if (func->Script.Num() > 0) {
		// goto 8(a uint32 value) to skip return
		uint8 code[] = { EX_JumpIfNot,8,0,0,0,Ex_LuaHook,EX_Return,EX_Nothing };
		func->Script.Insert(code, sizeof(code), 0);
	}
}
