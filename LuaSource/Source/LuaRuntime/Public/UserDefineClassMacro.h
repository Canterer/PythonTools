// Copyright 2020 Tencent Inc.  All rights reserved.
//
// Author: ruiqingkong@tencent.com
//
// 胶水层导出代码
// ...
#pragma once
#include "slua.h"
#include "log.h"
#include "LuaArray.h"
#include <type_traits>

struct LUARUNTIME_API LuaAutoRegistryClass {
	LuaAutoRegistryClass(NS_SLUA::lua_CFunction reg);
	static void reg(NS_SLUA::lua_State* L);
};

#define LUA_GLUE_CONCAT(a, b) a##b
#define LUA_GLUE_STR(a) #a

#define LUA_GLUE_TYPE(CLS) \
	NAMESPACE_NS_SLUA_BEGIN \
	template<> \
        SimpleString  TypeName<CLS>::value() { \
            return  SimpleString(#CLS); \
        } \
	NAMESPACE_NS_SLUA_END

// 胶水层导出开始部分
#define LUA_GLUE_BEGIN(CLS,...) \
        LUA_GLUE_TYPE(CLS) \
        static int Lua##CLS##_gc(NS_SLUA::lua_State* L) { \
             NS_SLUA::UserData<CLS*>* UD = reinterpret_cast< NS_SLUA::UserData<CLS*>*>(lua_touserdata(L,1)); \
            if(UD->flag & UD_AUTOGC) delete UD->ud; \
            return 0;\
        } \
        static int Lua##CLS##_tostring(NS_SLUA::lua_State* L) { \
            void* p =  NS_SLUA::lua_touserdata(L,1); \
            char buf[128]; \
            snprintf(buf,128,"%s(@%p)",#CLS,p); \
            NS_SLUA::lua_pushstring(L,buf); \
            return 1; \
        } \
		namespace LUA_GLUE_SPACE_##CLS \
		{ \
			using TheClass = CLS; \
			static int __Lua_##CLS##_setup( NS_SLUA::lua_State* L); \
			static LuaAutoRegistryClass __Lua_##CLS##_AutoRegistry__(__Lua_##CLS##_setup); \
			int __Lua_##CLS##_setup( NS_SLUA::lua_State* L) { \
				NS_SLUA::lua_CFunction TheClass_GC = Lua##CLS##_gc; \
				NS_SLUA::lua_CFunction TheClass_ToString = Lua##CLS##_tostring; \
				const char * TheClassName = #CLS; \
				static_assert(!std::is_base_of<UObject, CLS>::value, "UObject class shouldn't use LuaCppBinding. Use REG_EXTENSION instead."); \
				NS_SLUA::LuaObject::newTypeWithBase(L,#CLS,std::initializer_list<const char*>{#__VA_ARGS__});  

// 胶水层导出函数
// 参数：函数名字
// 示例：
// class A {
//    public:
//		void FuncA();
// };
// LUA_GLUE_BEGIN(A)
// LUA_GLUE_FUNCTION(FuncA)
// LUA_GLUE_END()
#define LUA_GLUE_FUNCTION(FunctionName) \
        { \
            NS_SLUA::lua_CFunction x= NS_SLUA::LuaCppBinding<decltype(&TheClass::FunctionName),&TheClass::FunctionName>::LuaCFunction; \
            constexpr bool inst=std::is_member_function_pointer<decltype(&TheClass::FunctionName)>::value; \
            NS_SLUA::LuaObject::addMethod(L, #FunctionName, x, inst); \
        }
// 胶水层导出函数的重载形式
// 参数：
//		FuncName:新的函数名字
//		ReplaceFunc: 替换后的函数
//		inst: 表示当前函数是成员函数还是静态函数
// 可以向类型里添加新的函数，也可以对现有类型进行重写
// 示例
// 为类型A添加一个新的成员函数
// class A {
// 
// };
// static int32 func(){return 0;};
// LUA_GLUE_BEGIN(A)
// LUA_GLUE_FUNCTION_OVERRIDE(new_func,func,true)
// LUA_GLUE_END()


#define LUA_GLUE_FUNCTION_OVERRIDE(FuncName,ReplaceFunc,inst) \
        { \
            NS_SLUA::lua_CFunction x= NS_SLUA::LuaCppBinding<decltype(&ReplaceFunc),&ReplaceFunc>::LuaCFunction; \
            NS_SLUA::LuaObject::addMethod(L, #FuncName, x, inst); \
        }

// 胶水层导出属性的访问
// 参数：
//		FIELD_NAME: 属性名字
#define LUA_GLUE_PROPERTY_GET(FIELD_NAME) \
    auto lua_get_##FIELD_NAME = [](NS_SLUA::lua_State* inL)->int32 \
    { \
        TheClass * Obj = NS_SLUA::LuaObject::checkUD<TheClass>(inL,1); \
        NS_SLUA::LuaObject::push(inL,Obj->FIELD_NAME); \
        return 1; \
    }; 
    
// 胶水层导出属性的设置
// 参数：
//		FIELD_NAME: 属性名字
#define LUA_GLUE_PROPERTY_SET(FIELD_NAME) \
    auto lua_set_##FIELD_NAME = [](NS_SLUA::lua_State* inL)->int32 \
    { \
        TheClass * Obj = NS_SLUA::LuaObject::checkUD<TheClass>(inL,1); \
        static_assert(!std::is_const<decltype(Obj->FIELD_NAME)>::value, "member is const,try LUA_GLUE_PROPERTY_GET"); \
		if(NS_SLUA::lua_type(inL,2) != LUA_TNIL) \
		{ \
			Obj->FIELD_NAME = NS_SLUA::LuaObject::checkValue<decltype(Obj->FIELD_NAME)>(inL,2); \
		} \
		else \
		{ \
			NS_SLUA::Log::Error("FiledName[%s] value is nil", TCHAR_TO_UTF8(#FIELD_NAME)); \
		} \
        return 1; \
    }; 
// 胶水层导出属性的访问
// 参数：
//		FIELD_NAME: 属性名字
#define LUA_GLUE_PROPERTY(FIELD_NAME) \
    { \
        LUA_GLUE_PROPERTY_GET(FIELD_NAME) \
        LUA_GLUE_PROPERTY_SET(FIELD_NAME) \
        NS_SLUA::LuaObject::addField(L, #FIELD_NAME, lua_get_##FIELD_NAME, lua_set_##FIELD_NAME, true); \
    }

// 胶水层导出数组类型属性的访问
// 参数：
//		FIELD_NAME: 属性名字
#define LUA_GLUE_PROPERTY_ARRAY_GET(FIELD_NAME) \
auto lua_get_##FIELD_NAME = [](NS_SLUA::lua_State* inL)->int32 \
    { \
        TheClass * Obj = NS_SLUA::LuaObject::checkUD<TheClass>(inL,1); \
		auto tn = NS_SLUA::TypeName<decltype(Obj->FIELD_NAME)>::value(); \
        NS_SLUA::LuaObject::push(inL,tn.c_str(),&Obj->FIELD_NAME,UD_NOFLAG); \
        return 1; \
    }; 


#define LUA_GLUE_PROPERTY_ARRAY_SET(FIELD_NAME) \
auto lua_set_##FIELD_NAME = [](NS_SLUA::lua_State* inL)->int32 \
    { \
		TheClass * Obj = NS_SLUA::LuaObject::checkUD<TheClass>(inL,1); \
		using ArrayType = decltype(Obj->FIELD_NAME); \
		auto ud = lua_touserdata(inL, 2); \
		auto udptr = reinterpret_cast<NS_SLUA::UserData<TArray<typename ArrayType::ElementType>*>*>(ud); \
		Obj->FIELD_NAME = *udptr->ud; \
		return 1; \
    }; 



// 胶水层导出数组类型属性
// 参数：
//		FIELD_NAME: 属性名字
#define LUA_GLUE_ARRAY_PROPERTY(FIELD_NAME) \
	{ \
		LUA_GLUE_PROPERTY_ARRAY_GET(FIELD_NAME) \
		LUA_GLUE_PROPERTY_ARRAY_SET(FIELD_NAME) \
		NS_SLUA::LuaObject::addField(L, #FIELD_NAME, lua_get_##FIELD_NAME, lua_set_##FIELD_NAME, true); \
	}

// 胶水层导出类型的默认构造函数
// 参数：
// 作用：方便在Lua层直接调用构造类型
#define LUA_GLUE_TEMP() \
    { \
        NS_SLUA::lua_CFunction x = [](NS_SLUA::lua_State * inL)->int32 \
        { \
            NS_SLUA::LuaObject::push(inL,NS_SLUA::TypeName<TheClass>::value().c_str(),new TheClass(),UD_AUTOGC); \
            return 1; \
        }; \
        NS_SLUA::LuaObject::addMethod(L,"Temp",x,false); \
    }

#define LUA_GLUE_GC(FunctionName) \
	{ \
		TheClass_GC = &TheClass::FunctionName;	\
	}

#define LUA_GLUE_END() \
        NS_SLUA::LuaObject::finishType(L,TheClassName, nullptr, TheClass_GC, TheClass_ToString); \
        return 0; } \
		} // LUA_GLUE_SPACE_##CLS

// 胶水层导出数组类型
// 参数：
//		CLS: 类型名字
// 作用：会在Lua层新建一个TArrat_CLS类型，来标记数组

#define LUA_GLUE_ARRAY(CLS) \
	NAMESPACE_NS_SLUA_BEGIN \
	template<> \
    SimpleString TypeName<TArray<CLS>>::value() { \
        return  SimpleString(LUA_GLUE_STR(TArray_##CLS)); \
    } \
	template<> \
    SimpleString TypeName<TArray<CLS *>>::value() { \
        return  SimpleString(LUA_GLUE_STR(TArray_##CLS)); \
    } \
	NAMESPACE_NS_SLUA_END \
	static int Lua_Array_##CLS##_gc(NS_SLUA::lua_State * L) {\
        NS_SLUA::UserData<CLS*>* UD = reinterpret_cast< NS_SLUA::UserData<CLS*>*>(lua_touserdata(L,1)); \
        if(UD->flag & UD_AUTOGC) delete UD->ud; \
        return 0;\
    } \
    static int Lua_Array_##CLS##_tostring(NS_SLUA::lua_State* L) { \
        void* p =  NS_SLUA::lua_touserdata(L,1); \
        char buf[128]; \
        snprintf(buf,128,"TArray<%s>(@%p)",#CLS,p); \
        NS_SLUA::lua_pushstring(L,buf); \
        return 1; \
    } \
	static int32 Lua_Array_##CLS##_setupmt(NS_SLUA::lua_State* L) { \
		return 0;\
	} \
	namespace LUA_GLUE_ARRAY_SPACE_##CLS \
	{ \
		static int __Lua_TArray_##CLS##_setup( NS_SLUA::lua_State* L); \
		static LuaAutoRegistryClass __Lua_TArray_##CLS##_AutoRegistry##__(__Lua_TArray_##CLS##_setup); \
		int __Lua_TArray_##CLS##_setup( NS_SLUA::lua_State* L) \
		{ \
			static_assert(!std::is_base_of<UObject, CLS>::value, "UObject class shouldn't use LuaCppBinding. Use REG_EXTENSION instead."); \
			const char * class_metatable_name = LUA_GLUE_STR(TArray_##CLS); \
			NS_SLUA::LuaObject::newType(L,class_metatable_name); \
			NS_SLUA::LuaObject::addOperator(L,"__index",FLuaArray::__index<CLS>); \
			NS_SLUA::LuaObject::addOperator(L,"__newindex",FLuaArray::__newindex<CLS>); \
			{ \
				NS_SLUA::lua_CFunction x = [](NS_SLUA::lua_State * inL)->int32{ \
					NS_SLUA::LuaObject::push(inL,LUA_GLUE_STR(TArray_##CLS),new TArray<CLS>(),UD_AUTOGC); \
					return 1; \
				}; \
				NS_SLUA::LuaObject::addMethod(L,"Temp",x,false); \
			}\
			{ \
				NS_SLUA::LuaObject::addMethod(L,"Add",&FLuaArray::Add<CLS>,true); \
				NS_SLUA::LuaObject::addMethod(L,"Num",&FLuaArray::Num<CLS>,true); \
				NS_SLUA::LuaObject::addMethod(L,"Sort",&FLuaArray::Sort<CLS>,true); \
			} \
			NS_SLUA::LuaObject::finishType(L,class_metatable_name, nullptr,  Lua_Array_##CLS##_gc, Lua_Array_##CLS##_tostring); \
			return 0; \
		} \
	}


// 封装UObjec UStruct类型的非导出函数的导出 

#define LUA_EXTENSION_STRUCT_TYPE(CLS) \
	NAMESPACE_NS_SLUA_BEGIN \
	template<> \
    SimpleString  TypeName<CLS>::value() { \
        return  SimpleString("LuaStruct"); \
    } \
    NAMESPACE_NS_SLUA_END \

#define LUA_EXTENSION_BEGIN(CLS,_IsLuaStruct) \
	namespace LUA_EXTENSION_SPACE_##CLS \
	{ \
		using TheClass = CLS; \
		static int __Lua_extension_##CLS##_setup(NS_SLUA::lua_State * L); \
		static LuaAutoRegistryClass __Lua_extension_##CLS##_AutoRegistry__(__Lua_extension_##CLS##_setup); \
		static bool IsLuaStruct = _IsLuaStruct; \
		int32 __Lua_extension_##CLS##_setup( NS_SLUA::lua_State* L) \
		{

#define LUA_EXTENSION_STRUCT(CLS) \
	LUA_EXTENSION_BEGIN(CLS,true)

#define LUA_EXTENSION_FUNCTION(FunctionName) \
	{ \
		using BindType = NS_SLUA::LuaCppBinding<decltype(&TheClass::FunctionName),&TheClass::FunctionName>; \
		if(IsLuaStruct) \
		{ \
			NS_SLUA::LuaObject::addExtensionMethod(TheClass::StaticStruct(), #FunctionName, BindType::LuaStructFunction, BindType::IsStatic); \
		} \
		else \
		{ \
			NS_SLUA::LuaObject::addExtensionMethod(TheClass::StaticStruct(), #FunctionName, BindType::LuaCFunction, BindType::IsStatic); \
		} \
	}

#define LUA_EXTENSION_END() \
			return 0; \
		}; \
	}
