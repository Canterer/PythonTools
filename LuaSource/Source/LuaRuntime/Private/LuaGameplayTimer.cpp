#include "LuaGameplayTimer.h"
#include "UserDefineClassMacro.h"
#include "LuaSubsystem.h"
#include "TimerManager.h"

extern UGameInstance* GetGameInstanceByLuaState(NS_SLUA::LuaState* LuaState);

namespace LuaGameplayTimer
{
USING_NAMESPACE_NS_SLUA

static int32 _timer_index = 0;
static TMap<int32, FTimerHandle> _timers;

int32 SetGameplayTimer(lua_State* inL)
{
	LuaState* LuaState = LuaState::get(inL);
	if(!LuaState)
		return 0;
	const UGameInstance* GameInstance = GetGameInstanceByLuaState(LuaState);
	if(!IsValid(GameInstance))
		return 0;

	if(!lua_isnumber(inL, 1) || !lua_isboolean(inL, 2) || !lua_isfunction(inL, 3))
	{
		luaL_error(inL, "Timer: param error set");
		return 0;
	}
	
	const float Interval = LuaObject::checkValue<float>(inL, 1);
	const bool bLoop = LuaObject::checkValue<bool>(inL, 2);
	LuaVar CallBack(inL, 3);

	FTimerDelegate TimerDelegate;
	TimerDelegate.BindLambda([CallBack]() {CallBack.call(); });
	
	FTimerHandle Handler;
	GameInstance->GetTimerManager().SetTimer(Handler, TimerDelegate, Interval, bLoop);
	++_timer_index;
	_timers.Add(_timer_index, Handler);
	return LuaObject::push(inL, _timer_index);
}

int32 ClearGameplayTimer(lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	LuaState* LuaState = LuaState::get(inL);
	if(!LuaState)
		return 0;
	const UGameInstance* GameInstance = GetGameInstanceByLuaState(LuaState);
	if(!IsValid(GameInstance))
		return 0;

	if(!lua_isnumber(inL, 1))
	{
		// luaL_error(inL, "Timer: param error clear");
		return 0;
	}
	
	int32 Index = LuaObject::checkValue<int32>(inL, 1);
	if(FTimerHandle* Handler = _timers.Find(Index))
	{
		GameInstance->GetTimerManager().ClearTimer(*Handler);
		_timers.Remove(Index);
	}
	return 0;
}

void Open(lua_State* inL)
{
	lua_newtable(inL);

	luaL_Reg all_functions [] = {
		{"SetTimer",&SetGameplayTimer},
		{"ClearTimer",&ClearGameplayTimer},
		{NULL,NULL}
	};
	luaL_setfuncs(inL,all_functions,0);

	lua_setglobal(inL,"GameplayTimer");
}
}
