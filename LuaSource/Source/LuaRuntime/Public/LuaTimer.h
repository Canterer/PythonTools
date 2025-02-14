#pragma once
#include "Tickable.h"
#include "slua.h"

enum ELuaTimerState
{

	Pending = 1,
	Active = 2,
	Execute = 3,
	Pause = 4,
	End,
};

struct FLuaTimerHandle
{
public:
	FLuaTimerHandle() :Rate(-1) {}

	NS_SLUA::LuaVar LuaRef;
	float ExpireTime = 0;
	float Rate = 0;
	uint32 CallNum = 0; // 0 loop
	uint32 CallCount = 0;
	ELuaTimerState State;
	int32 TimerId = -1;
};

template <>
struct TLess<FLuaTimerHandle>
{
	FORCEINLINE bool operator()(const FLuaTimerHandle& A, const FLuaTimerHandle& B) const
	{
		return A.ExpireTime < B.ExpireTime;
	}
};

class FLuaTimerManager : public FTickableGameObject
{
public:
	FLuaTimerManager();
	virtual TStatId GetStatId() const override;
	virtual void Tick(float DeltaTime) override;
	void Open(NS_SLUA::lua_State* inL);
	void Close();
	int32 SetTimer(NS_SLUA::lua_State* inL);
	int32 ClearTimer(NS_SLUA::lua_State* inL);
	int32 SetNum(NS_SLUA::lua_State* inL);
	int32 SetRate(NS_SLUA::lua_State* inL);

	virtual bool IsTickable() const override
	{
		return bTickEnable;
	}
private:
	void InnerInsertPendingTimer(FLuaTimerHandle& InTimeHandle);
	void InnerInsertActiveTimer(FLuaTimerHandle& InTimeHandle);
	
	int32 AllocTimerId();
	FLuaTimerHandle* FindLuaTimeHandle(int32 LuaRef);
private:

	TArray<FLuaTimerHandle> ActiveTimerHeap;
	TArray<FLuaTimerHandle> PendingTime;
	
	int32 TimerCount;
	
	bool bTickStart;

	FLuaTimerHandle CurrentExecute;
	int32 LuaTimeTableIndex;
	bool bTickEnable = false;
};

class FLuaTimerHelper
{
public:
	static int32 SetTimer(NS_SLUA::lua_State* inL);
	static int32 ClearTimer(NS_SLUA::lua_State* inL);
	static int32 SetNum(NS_SLUA::lua_State* inL);
	static int32 SetRate(NS_SLUA::lua_State* inL);
};

