#include "UnrealLuaInterface.h"
#include "CoreMinimal.h"

int32 UUnrealLuaInterface::RunLuaCode(UObject* LuaWorld, FString const& InLuaCode)
{
	if(LuaWorld == nullptr || LuaWorld->GetWorld() == nullptr)
	{
		return -1;
	}

	NS_SLUA::lua_State * L = ULuaSubSystem::GetThreadLuaState(LuaWorld);

	if(L == nullptr)
	{
		return -2;
	}

	int32 current_luastate = NS_SLUA::lua_status(L);
	if(current_luastate != LUA_OK)
	{
		return -3;
	}
	NS_SLUA::luaL_loadstring(L,TCHAR_TO_ANSI(*InLuaCode));
	
	int32 error_code = NS_SLUA::lua_resume(L,nullptr,0);
	
	if(error_code != 0)
	{ 
		return error_code;
	}

	return 0;
	
}
