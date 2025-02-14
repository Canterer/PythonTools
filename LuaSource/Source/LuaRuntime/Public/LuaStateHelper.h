#pragma once
#include "slua.h"
class FLuaStateHelper
{
public:
	static int32 PushAll(NS_SLUA::lua_State * inL){ return 0;};
	template<typename T, typename...Args>
	static int32 PushAll(NS_SLUA::lua_State* inL, const T& first, Args...args)
	{
		USING_NAMESPACE_NS_SLUA
		LuaObject::push(inL, first);
		FLuaStateHelper::PushAll(inL, args...);

		return sizeof...(args);
	}

	
};
