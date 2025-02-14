#pragma once
#include "slua.h"
class FLuaArrayHelper
{
public:
	

	template<typename T>
	static TArray<T> const & pop(NS_SLUA::lua_State * inL,int32 index)
	{
		USING_NAMESPACE_NS_SLUA

		auto ud = lua_touserdata(inL, index);

		auto udptr = reinterpret_cast<UserData<TArray<T>*>*>(ud);

		return *udptr->ud;
	}
};

class FLuaArray
{
public:
	template<class T>
	static int32 Add(NS_SLUA::lua_State * inL)
	{
		auto tarray = reinterpret_cast<NS_SLUA::UserData<TArray<T>*>*>(lua_touserdata(inL, 1));
		TArray<T> * array_ptr = tarray->ud;
		if(array_ptr)
		{
			auto item = reinterpret_cast<NS_SLUA::UserData<T*>*>(lua_touserdata(inL, 2));
			array_ptr->Add(*(item->ud));
		}

		return 0;
	}
	template<class T>
	static int32 Num(NS_SLUA::lua_State * inL)
	{
		auto tarray = reinterpret_cast<NS_SLUA::UserData<TArray<T>*>*>(lua_touserdata(inL, 1));
		if(tarray)
		{
			TArray<T>* array_ptr = tarray->ud;
			if (array_ptr)
			{
				NS_SLUA::LuaObject::push(inL, array_ptr->Num());
				return 1;
			}
		}
		return 0;
	}

	template<class T>
	static int32 __index(NS_SLUA::lua_State * inL)
	{
		USING_NAMESPACE_NS_SLUA
		if(lua_type(inL,2) == LUA_TNUMBER)
		{
			int32 index = NS_SLUA::LuaObject::checkValue<int32>(inL,2);
			auto tarray = reinterpret_cast<NS_SLUA::UserData<TArray<T>*>*>(lua_touserdata(inL, 1));
			if (tarray)
			{
				TArray<T>* array_ptr = tarray->ud;
				if (array_ptr && array_ptr->IsValidIndex(index - 1))
				{
					T const & item = (*array_ptr)[index - 1];
					NS_SLUA::LuaObject::push(inL,&item);
					return 1;
				}
			}

			return 0;
		}
		return NS_SLUA::LuaObject::classIndex(inL);
	}

	template<class T>
	static int32 __newindex(NS_SLUA::lua_State * inL)
	{
		USING_NAMESPACE_NS_SLUA
		if (lua_type(inL, 2) == LUA_TNUMBER)
		{
			int32 index = NS_SLUA::LuaObject::checkValue<int32>(inL, 2);
			auto tarray = reinterpret_cast<NS_SLUA::UserData<TArray<T>*>*>(lua_touserdata(inL, 1));
			auto value_ptr = reinterpret_cast<NS_SLUA::UserData<T*>*>(lua_touserdata(inL, 3));
			if (tarray)
			{
				TArray<T>* array_ptr = tarray->ud;
				if(array_ptr)
				{
					if(array_ptr->Num() > index - 1)
					{
						(*array_ptr)[index - 1] = *(value_ptr->ud);
						return 1;
					}
					else if(array_ptr->Num() == index - 1)
					{
						array_ptr->Emplace(*(value_ptr->ud));
					}
					
				}
				
				
			}

			return 0;
		}
		return NS_SLUA::LuaObject::classNewindex(inL);
	}

	template<typename T>
	static int32 Sort(NS_SLUA::lua_State * inL)
	{
		USING_NAMESPACE_NS_SLUA
		auto tarray = reinterpret_cast<NS_SLUA::UserData<TArray<T>*>*>(lua_touserdata(inL, 1));
		if(tarray)
		{
			TArray<T>* array_ptr = tarray->ud;
			if(array_ptr)
			{
				if(lua_type(inL,2) == LUA_TFUNCTION)
				{
					LuaVar lua_compare = LuaVar(inL,2,LuaVar::Type::LV_FUNCTION);
					auto lambda_compare = [&inL,&lua_compare](T const & InLeft,T const & InRight) -> bool {
						LuaVar result = lua_compare.call<int32>(InLeft,InRight);
						return result.asInt() > 0;
					};
					array_ptr->Sort(lambda_compare);
				}
				else if(lua_type(inL,2) == LUA_TTABLE)
				{
					// __call metatable
				}
				else
				{
					//array_ptr->Sort();
				}
				
			}
		}

		return 0;


	}
};
