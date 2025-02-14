#include "Glue/BaseEngineGlue.h"
#include "slua.h"
#include "Misc/ConfigCacheIni.h"
#include "LuaArray.h"
#include "CoreGlobals.h"


static int32 GetGlobalConfig(NS_SLUA::lua_State * inL)
{
	NS_SLUA::LuaObject::push(inL,new FNZLuaConfigCacheIniWrap(GConfig));
	return 1;
}

static int32 LoadGloablIni(NS_SLUA::lua_State * inL)
{
	const char * IniName = NS_SLUA::LuaObject::checkValue<const char *>(inL,1);
	FString FinalName;
	FConfigCacheIni::LoadGlobalIniFile(FinalName,UTF8_TO_TCHAR(IniName));

	NS_SLUA::LuaObject::push(inL,FinalName);

	return 1;
}


FNZLuaConfigCacheIniWrap::FNZLuaConfigCacheIniWrap(FConfigCacheIni * InInnerConfig) : InnerConfig(InInnerConfig)
{

}
FNZLuaConfigCacheIniWrap::~FNZLuaConfigCacheIniWrap()
{
	InnerConfig = nullptr;
}

TArray<FString> FNZLuaConfigCacheIniWrap::GetArray(FString const & SectionName,FString const & KeyName ,FString const & IniName)
{
	TArray<FString> outArray;
	if(InnerConfig)
	{
		InnerConfig->GetArray(*SectionName,*KeyName,outArray,IniName);
	}

	return outArray;
}

FString FNZLuaConfigCacheIniWrap::GetString( const FString& Section, const FString& Key, const FString& Filename )
{
	FString result;
	if(InnerConfig)
	{
		InnerConfig->GetString(*Section,*Key,result,Filename);
	}

	return result;
}

NAMESPACE_NS_SLUA_BEGIN
	DefLuaClass(FConfigFile)
	
	EndDef(FConfigFile,nullptr)

	DefLuaClass(FConfigCacheIni)
		DefLuaMethod(LoadGloablIni,&LoadGloablIni)
		DefLuaMethod(GetGlobalConfig, &GetGlobalConfig)
	EndDef(FConfigCacheIni,nullptr)


	DefLuaClass(FNZLuaConfigCacheIniWrap)
		DefLuaMethod(GetArray, &FNZLuaConfigCacheIniWrap::GetArray)
		DefLuaMethod(GetString, &FNZLuaConfigCacheIniWrap::GetString)
	EndDef(FNZLuaConfigCacheIniWrap,nullptr)
NAMESPACE_NS_SLUA_END

