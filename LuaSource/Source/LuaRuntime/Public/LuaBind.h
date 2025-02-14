#pragma once
#include "CoreMinimal.h"
#include "Templates/SharedPointer.h"
#include "slua.h"
#include "LuaVar.h"
#include "LuaStateHelper.h"
#include "LuaSubsystem.h"

#include <lua.h>

class LUARUNTIME_API FLuaBindBridge
{
public:
	template<class T>
	static void dispose(const T* ptrT)
	{
		USING_NAMESPACE_NS_SLUA
		ensure(ptrT);
		UGameInstance* GameIns = getGameInstance(ptrT);
		if (!GameIns)
			return;
		auto ls = NS_SLUA::LuaState::get(GameIns);
		if (!ls)
			return;
		auto L = ls->getLuaState();
		if (!L)
			return;

		int32 BindRef = ULuaSubSystem::GetCacheBindRef(GameIns);
		if (BindRef != LUA_NOREF)
		{
			lua_rawgeti(L,LUA_REGISTRYINDEX, BindRef);
			{
				lua_rawgetp(L, -1, ptrT);
				if (lua_istable(L, -1))
				{
					// call release
					{
						lua_pushstring(L, "OnDestroy");
						lua_rawget(L, -2); // t func
						{
							NS_SLUA::LuaVar lfunc(L, -1);
							lua_pushvalue(L, -2); // func t
							lfunc.callWithNArg(1);
						}
						lua_pop(L, 1);
					}
					// end call
					lua_pushnil(L);
					lua_setfield(L, -2, SLUA_CPPINST);
				}
				lua_pop(L, 1);
			}
			lua_pushnil(L);
			lua_rawsetp(L, -2, ptrT);
			lua_pop(L, 1);

			ensureAlways(lua_gettop(L) == 0);
		}
	}

	template<class T, bool F = TIsDerivedFrom<T, UObject>::IsDerived>
	static UGameInstance* getGameInstance(const T* ptrT)
	{
		if (F)
		{
			if (ptrT->GetWorld())
			{
				return ptrT->GetWorld()->GetGameInstance();
			}
		}
		return nullptr;
	}

	static NS_SLUA::lua_State * getLuaState(const UObject * ptrT)
	{
		UGameInstance* GameIns = getGameInstance(ptrT);
		if (!GameIns)
			return nullptr;
		auto ls = NS_SLUA::LuaState::get(GameIns);
		if (!ls)
			return nullptr;
		auto L = ls->getLuaState();
		if (!L)
			return nullptr;
		return L;
	}


	static int __index(NS_SLUA::lua_State* L);

	static int __newindex(NS_SLUA::lua_State* L);

	#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
	static void hookBpScript(UFunction* func, FNativeFuncPtr hookfunc);
	#else
	static void hookBpScript(UFunction* func, Native hookfunc);
	#endif

	template<class T>
	static void bindOverrideFunc(NS_SLUA::lua_State* inL, int32 const TableIndex, const T*)
	{
	}

	static void bindOverrideFunc(NS_SLUA::lua_State* inL, int32 const TableIndex, UObject*);

	DECLARE_FUNCTION(luaOverrideFunc);


	template<class T>
	static bool init(const T* ptrT, FString const& luaPath)
	{
		USING_NAMESPACE_NS_SLUA

		if (luaPath.IsEmpty())
			return false;

		ensure(ptrT);
		UGameInstance* GameIns = getGameInstance(ptrT);
		if (!GameIns)
			return false;

		auto ls = NS_SLUA::LuaState::get(GameIns);
		if (!ls)
			return false;
		
		auto L = ls->getLuaState();
		if (!L)
			return false;

		ensureAlwaysMsgf(lua_gettop(L) == 0, TEXT("Top %d type %d"), lua_gettop(L), lua_type(L,1));

		NS_SLUA::LuaVar luaSelfTable = ls->doFile(TCHAR_TO_UTF8(*luaPath));
		if (!luaSelfTable.isTable())
			return false;

		luaSelfTable.push(L);
		

		lua_pushlightuserdata(L, (void*)ptrT);
		lua_setfield(L, -2, SLUA_CPPINST);
		bindOverrideFunc<T>(L, -1, ptrT);
		

		if (luaL_newmetatable(L, "LuaBind") == 1)
		{
			lua_pushcfunction(L, __index);
			lua_setfield(L, -2, "__index");
			lua_pushcfunction(L, __newindex);
			lua_setfield(L, -2, "__newindex");
		}

		lua_setmetatable(L, -2);
		

		// ptrt,table
		int32 BindRef = ULuaSubSystem::GetCacheBindRef(GameIns);
		if (BindRef != LUA_NOREF)
		{
			lua_rawgeti(L,LUA_REGISTRYINDEX, BindRef);
			lua_pushvalue(L, -2);
			lua_rawsetp(L, -2, ptrT);
			lua_pop(L, 1);
		}
		
		//
		{
			lua_pushstring(L, "Initialize");
			lua_rawget(L, -2); // t func
			{
				NS_SLUA::LuaVar lfunc(L, -1);
				lua_pushvalue(L, -2); // func t
				lfunc.callWithNArg(1);
			}
			lua_pop(L, 1);
		}
		lua_pop(L, 1);
		ensureAlwaysMsgf(lua_gettop(L) == 0, TEXT("Top %d"), lua_gettop(L));
		return true;
	}

	template<class T, class...Args>
	static NS_SLUA::LuaVar Call(const T* ptrT, const char* func, Args ...args)
	{
		USING_NAMESPACE_NS_SLUA
		ensure(ptrT);
		UGameInstance* GameIns = getGameInstance(ptrT);
		
		auto L = getLuaState(ptrT);
		if (!L)
			return NS_SLUA::LuaVar();

		int32 BindRef = ULuaSubSystem::GetCacheBindRef(GameIns);
		if (BindRef != LUA_NOREF)
		{
			lua_rawgeti(L,LUA_REGISTRYINDEX, BindRef); // 1
			lua_rawgetp(L, -1, ptrT);                  // 2
			if (lua_istable(L, -1))
			{
				lua_pushstring(L, func);
				lua_rawget(L, -2); // 3 func
				NS_SLUA::LuaVar lfunc(L, -1);
				lua_pushvalue(L, -2);

				FLuaStateHelper::PushAll(L, args...);
				const int32 ParamCount = sizeof...(args);

				NS_SLUA::LuaVar Result = lfunc.callWithNArg(ParamCount + 1);

				lua_pop(L, 3);
				//ensureAlways(lua_gettop(L) == 0);
				return Result;
			}
			lua_pop(L, 2);
		}
		//ensureAlways(lua_gettop(L) == 0);
		return NS_SLUA::LuaVar();
	}

	template<class T>
	static void AddMethod(const T* ptrT, const char* InFuncName,NS_SLUA::lua_CFunction func)
	{
		USING_NAMESPACE_NS_SLUA
		ensure(ptrT);
		UGameInstance* GameIns = getGameInstance(ptrT);
		if (!GameIns)
			return;
		
		auto L = getLuaState(ptrT);
		if (!L)
			return;

		int32 BindRef = ULuaSubSystem::GetCacheBindRef(GameIns);
		if (BindRef != LUA_NOREF)
		{
			lua_rawgeti(L,LUA_REGISTRYINDEX, BindRef);
			lua_rawgetp(L, -1, ptrT);
			if (lua_istable(L, -1))
			{
				lua_pushstring(L, InFuncName);
				lua_pushcfunction(L, func);
				lua_rawset(L, -3);
			}
			lua_pop(L, 2);
		}
		ensureAlways(lua_gettop(L) == 0);
	}

/*
 * Push和CallAndPop应该成对出现，用于自己压栈数据的操作。使用起来应该看起来像这样：
	auto inL = FLuaBindBridge::Push(this, "ProtoProcess");
	if (inL)
	{
		// your push param action
		FLuaBindBridge::CallAndPop(this, 2);
	}
 */
	
	
};


#define LuaCtor(LuaFilePath,ptrT) \
	{ \
		UWorld * TheWorld = this->GetWorld(); \
		FLuaBindBridge::init(ptrT,LuaFilePath); \
	}

#define LuaAddMethod(ptrT,FunctionName,Func) \
	{ \
		NS_SLUA::lua_CFunction x= NS_SLUA::LuaCppBinding<decltype(Func),Func>::LuaCFunction; \
		FLuaBindBridge::AddMethod(ptrT,#FunctionName,x); \
	}

#define LuaCall(ptr,FuncName,...) \
	{ \
		FLuaBindBridge::Call(ptr,FuncName,##__VA_ARGS__); \
	}

#define LuaRelease(ptrT) \
	{ \
		FLuaBindBridge::dispose(ptrT); \
	}
	

//#define LuaCallOtherObjectMemberFunc(FuncName,PtrT,...) \
// 	NS_SLUA::LuaState * ls = NS_SLUA::LuaState::get(FLuaBindBridge::getGameInstance(PtrT)); \
// 	if (ls) \
// 	{ \
// 		NS_SLUA::lua_State * inL = ls->getLuaState(); \
// 		if(inL) \
// 		{ \
// 			NS_SLUA::LuaObject::push(inL,PtrT); \
// 			if(NS_SLUA::lua_type(inL,-1) == LUA_TTABLE) \
// 			{ \
// 				NS_SLUA::lua_pushstring(inL,FuncName); \
// 				NS_SLUA::lua_gettable(inL,-2); \
// 				if(LUA_TFUNCTION == NS_SLUA::lua_type(inL,-1)) \
// 				{ \
// 					lua_insert(inL,-2); \
// 					const int32 ParamCount = FLuaStateHelper::PushAll(inL, ##__VA_ARGS__); \
// 					lua_call(inL,ParamCount + 1,0); \
// 				} \
// 			} \
// 		} \
// 	}
