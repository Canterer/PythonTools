#include "LuaTimer.h"
#include "UserDefineClassMacro.h"

static bool ShouldCallOnceInTick = true;

FLuaTimerManager::FLuaTimerManager() : FTickableGameObject()
{
	bTickEnable = false;
	TimerCount = 0;
}

void FLuaTimerManager::Open(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	lua_newtable(inL);

	lua_pushlightuserdata(inL,this);
	
	luaL_Reg all_functions [] = {
		{"SetTimer",&FLuaTimerHelper::SetTimer},
		{"SetRate",&FLuaTimerHelper::SetRate},
		{"SetNum",&FLuaTimerHelper::SetNum},
		{"ClearTimer",&FLuaTimerHelper::ClearTimer},
		{NULL,NULL}
	};
	luaL_setfuncs(inL,all_functions,1);

	lua_setglobal(inL,"FLuaTimerHelper");
	bTickEnable = true;
}

void FLuaTimerManager::Close()
{
	bTickEnable = false;
}

TStatId FLuaTimerManager::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(LuaStatTimerTick, STATGROUP_Tickables)
}

void FLuaTimerManager::Tick(float DeltaTime)
{
	if (!bTickEnable)
	{
		return;
	}
	bTickStart = true;


	while (ActiveTimerHeap.Num() > 0)
	{
		FLuaTimerHandle& Top = ActiveTimerHeap.HeapTop();
		if (Top.State == ELuaTimerState::Active && Top.ExpireTime < DeltaTime)
		{
			ActiveTimerHeap.HeapPop(CurrentExecute);

			int32 CallCountInTick = 1;

			if (!ShouldCallOnceInTick)
			{
				CallCountInTick = FMath::TruncToInt((CurrentExecute.ExpireTime) / CurrentExecute.Rate) + 1;

				if (CurrentExecute.CallNum > 0)
				{
					if (CallCountInTick + CurrentExecute.CallCount > CurrentExecute.CallNum)
					{
						CallCountInTick = CurrentExecute.CallNum - CurrentExecute.CallCount;
					}
				}
			}
			CurrentExecute.State = Execute;
			int32 I = 0;
			for (; I < CallCountInTick && CurrentExecute.State == ELuaTimerState::Execute; ++I)
			{
				CurrentExecute.LuaRef.call();
			}
			if (CurrentExecute.CallNum > 0)
			{
				CurrentExecute.CallCount += I;
				if (CurrentExecute.CallCount >= CurrentExecute.CallNum)
				{
					CurrentExecute.State = End;
				}
			}

			if (ELuaTimerState::Execute == CurrentExecute.State)
			{
				if (!ShouldCallOnceInTick)
				{
					CurrentExecute.ExpireTime += I * CurrentExecute.Rate;
				}
				else
				{
					int32 CallCount = FMath::TruncToInt((DeltaTime - CurrentExecute.ExpireTime) / CurrentExecute.Rate) + 1;
					CurrentExecute.ExpireTime += CallCount * CurrentExecute.Rate;
				}
				InnerInsertActiveTimer(CurrentExecute);
			}
		}
		else
		{
			break;
		}
	}


	CurrentExecute.LuaRef = LUA_NOREF;

	TArray<int32> ShouldToRemoveIndex;
	for (int32 i = 0; i < ActiveTimerHeap.Num(); ++i)
	{
		if (ActiveTimerHeap[i].State == End)
		{
			ShouldToRemoveIndex.Add(i);
		}
		else
		{
			if (ActiveTimerHeap[i].ExpireTime > DeltaTime)
			{
				ActiveTimerHeap[i].ExpireTime -= DeltaTime;
			}
			else
			{
				ActiveTimerHeap[i].ExpireTime = 0;
			}
		}
		//
	}
	bTickStart = false;


	for (int32 i = ShouldToRemoveIndex.Num() - 1; i >= 0; --i)
	{
		ActiveTimerHeap.RemoveAt(ShouldToRemoveIndex[i]);
	}
	if (ShouldToRemoveIndex.Num() > 0)
	{
		ActiveTimerHeap.HeapSort();
	}

	for (int32 Index = 0; Index < PendingTime.Num(); Index++)
	{
		if (PendingTime[Index].Rate > 0 && PendingTime[Index].State != End)
		{
			PendingTime[Index].ExpireTime = PendingTime[Index].Rate;
			InnerInsertActiveTimer(PendingTime[Index]);
		}
	}
	PendingTime.RemoveAll([](FLuaTimerHandle const& Item) {
		return Item.Rate > 0 || Item.State == ELuaTimerState::End;
	});
}


int32 FLuaTimerManager::SetTimer(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA

	ensureAlways(lua_type(inL, 1) == LUA_TFUNCTION);
	
	FLuaTimerHandle Handle;

	Handle.LuaRef = LuaVar(inL,1,LuaVar::LV_FUNCTION);
	Handle.Rate = 0;
	Handle.CallCount = 0;
	Handle.CallNum = 0;
	Handle.ExpireTime = 0;
	Handle.TimerId = AllocTimerId();
	InnerInsertPendingTimer(Handle);

	return Handle.TimerId;
}

int32 FLuaTimerManager::AllocTimerId()
{
	TimerCount += 1;
	check(TimerCount < MAX_int32);
	return TimerCount;
}
int32 FLuaTimerManager::ClearTimer(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	int32 TimerId = LuaObject::checkValue<int32>(inL, 1);
	if(TimerId == CurrentExecute.TimerId)
	{
		CurrentExecute.State = ELuaTimerState::End;
	}
	else
	{
		FLuaTimerHandle* Handle = FindLuaTimeHandle(TimerId);
		if(Handle)
		{
			Handle->State = ELuaTimerState::End;
		}
	}
	return 0;
}
FLuaTimerHandle* FLuaTimerManager::FindLuaTimeHandle(int32 InLuaTimerId)
{
	for (FLuaTimerHandle& Item : PendingTime)
	{
		if (Item.TimerId == InLuaTimerId)
		{
			return &Item;
		}
	}
	for (FLuaTimerHandle& Item : ActiveTimerHeap)
	{
		if (Item.TimerId == InLuaTimerId)
		{
			return &Item;
		}
	}

	return nullptr;
}


int32 FLuaTimerManager::SetNum(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA

	int32 TimerId = LuaObject::checkValue<int32>(inL, 1);
	int32 CallNum = LuaObject::checkValue<int32>(inL, 2);

	if(CurrentExecute.TimerId == TimerId)
	{
		CurrentExecute.CallNum = CallNum;
	}
	else
	{
		FLuaTimerHandle* Handle = FindLuaTimeHandle(TimerId);
		if (Handle)
		{
			Handle->CallNum = CallNum;
		}
		ActiveTimerHeap.HeapSort();
	}
	return 0;
}

int32 FLuaTimerManager::SetRate(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	int32 TimerId = LuaObject::checkValue<int32>(inL,1);
	float Rate = LuaObject::checkValue<float>(inL,2);
	if(bTickStart)
	{
		if(CurrentExecute.TimerId == TimerId)
		{
			CurrentExecute.Rate = Rate;
		}
		else
		{
			FLuaTimerHandle* Handle = FindLuaTimeHandle(TimerId);
			if(Handle)
			{
				Handle->Rate = Rate;
			}
			ActiveTimerHeap.HeapSort();
		}	
	}
	else
	{
		FLuaTimerHandle* Handle = FindLuaTimeHandle(TimerId);
		if (Handle)
		{
			Handle->Rate = Rate;
		}
		ActiveTimerHeap.HeapSort();
	}
	return 0;
}


void FLuaTimerManager::InnerInsertPendingTimer(FLuaTimerHandle& InTimeHandle)
{
	InTimeHandle.State = ELuaTimerState::Pending;
	PendingTime.Add(InTimeHandle);
}

void FLuaTimerManager::InnerInsertActiveTimer(FLuaTimerHandle& InTimeHandle)
{
	InTimeHandle.State = ELuaTimerState::Active;
	ActiveTimerHeap.HeapPush(InTimeHandle);
}


int32 FLuaTimerHelper::SetTimer(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	FLuaTimerManager * TimerManager = (FLuaTimerManager *)lua_touserdata(inL,lua_upvalueindex(1));
	if(TimerManager)
	{
		int32 LuaRef = TimerManager->SetTimer(inL);
		lua_pushinteger(inL, LuaRef);
		return 1;
	}

	return 0;
}

int32 FLuaTimerHelper::ClearTimer(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	FLuaTimerManager * TimerManager = (FLuaTimerManager *)lua_touserdata(inL,lua_upvalueindex(1));

	if (TimerManager)
	{
		TimerManager->ClearTimer(inL);
	}
	return 0;
}

int32 FLuaTimerHelper::SetNum(NS_SLUA::lua_State* inL)
{
	USING_NAMESPACE_NS_SLUA
	FLuaTimerManager * TimerManager = (FLuaTimerManager *)lua_touserdata(inL,lua_upvalueindex(1));
	if (TimerManager)
	{
		TimerManager->SetNum(inL);
	}
	return 0;
}

int32 FLuaTimerHelper::SetRate(NS_SLUA::lua_State* inL)
{
	FLuaTimerManager* TimerManager = (FLuaTimerManager *)lua_touserdata(inL,lua_upvalueindex(1));
	if (TimerManager)
	{
		TimerManager->SetRate(inL);
	}
	return 0;
}

