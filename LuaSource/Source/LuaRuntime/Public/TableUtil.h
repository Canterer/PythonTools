#pragma once
#include "slua.h"
class UTableUtil
{
public:
	template<typename T>
	static void read(T & outValue, NS_SLUA::lua_State* inL, int32 index)
	{
		outValue = NS_SLUA::LuaObject::checkValue<T>(inL,index);
	}
	template<class T>
	static void push_ret(NS_SLUA::lua_State * inL,T * value)
	{
		NS_SLUA::LuaObject::push(inL,value);
	}

	template<class T>
	static void push_ret(NS_SLUA::lua_State* inL, T const & value)
	{
		NS_SLUA::LuaObject::push(inL, value);
	}
};

template<>
inline void UTableUtil::read(FString & outValue,NS_SLUA::lua_State * inL,int32 index)
{
	const char* buf = NS_SLUA::LuaObject::checkValue<const char*>(inL, index);
	if (buf)
	{
		outValue = UTF8_TO_TCHAR(buf);
	}
}

template<>
inline void UTableUtil::read(UObject * & outValue, NS_SLUA::lua_State* inL, int32 index)
{
	outValue = NS_SLUA::LuaObject::checkUD<UObject>(inL,index);
}

template<>
inline void UTableUtil::read(FSoftObjectPath& outValue, NS_SLUA::lua_State* inL, int32 index)
{
	const char* buf = NS_SLUA::LuaObject::checkValue<const char*>(inL, index);
	if(buf)
	{
		outValue.SetPath(UTF8_TO_TCHAR(buf));
	}
}
