#include "LuaSubsystem.h"

#include "GMMessageHelper.h"
#include "LuaGameplay.h"
#include "LuaRuntimeModule.h"
#include "LuaSetting.h"
#include "UserDefineClassMacro.h"
#include "Engine/Engine.h"

DECLARE_LOG_CATEGORY_CLASS(LuaSubsystem, Log, Log);

FOnLuaStateDelegate ULuaSubSystem::OnLuaStateInitCallback;
FOnLuaStateDelegate ULuaSubSystem::OnLuaStateCloseCallback;

static TMap<NS_SLUA::LuaState*, TWeakObjectPtr<UGameInstance>> LuaState2GameInstance;

UGameInstance* GetGameInstanceByLuaState(NS_SLUA::LuaState* LuaState)
{
	if(const auto& Ins = LuaState2GameInstance.Find(LuaState))
	{
		return Ins->Get();
	}
	return nullptr;
}


FLuaStateWrapper::FLuaStateWrapper(const char* InStateName) :TheSLuaState(InStateName)
{
	
}

void ULuaSubSystem::Initialize(FSubsystemCollectionBase& Collection)
{
	UE_LOG(LuaSubsystem,Log,TEXT("LuaSubSystem::Initialize"));
	Super::Initialize(Collection);
#if !UE_SERVER
	UGameInstance * GameIns = Cast<UGameInstance>(GetOuter());
	if(GameIns)
	{
		FWorldContext * ThisWorldContext = GameIns->GetWorldContext();
		if(ThisWorldContext && ThisWorldContext->World() )
		{
			if(ThisWorldContext->RunAsDedicated == false)
			{
				FString StateName = FString::Printf(TEXT("GameIns:%p"),GameIns);
				MainStateWrapper = MakeShareable(new FLuaStateWrapper(TCHAR_TO_UTF8(*StateName)));
				MainStateWrapper->GameIns = GameIns;
			}
		}
	}
	FGMMessageHelper::ListenObjectMessage(GameIns, MSGKEY("OnGameModeCreated"), this, [](AGameModeBase* GameMode){FGPLuaGameplay::Get().OnGameModeCreated(GameMode);});
#endif
}

int32 ULuaSubSystem::GetCacheBindRef(const UGameInstance * InGameIns)
{
	if(InGameIns)
	{
		ULuaSubSystem * SubSystem = UGameInstance::GetSubsystem<ULuaSubSystem>(InGameIns);
		if(SubSystem)
		{
			if(SubSystem->MainStateWrapper.IsValid())
			{
				return SubSystem->MainStateWrapper->WorldRef;
			}
		}
	}
	

	return LUA_NOREF;
}

NS_SLUA::lua_State* ULuaSubSystem::GetThreadLuaState(const UObject* InWorldContext)
{
	UWorld * InWorld = nullptr;
	if(InWorldContext)
	{
		InWorld = InWorldContext->GetWorld();
	}
	if(InWorld && InWorld->GetGameInstance())
	{
		ULuaSubSystem * LuaSubSystem = InWorld->GetGameInstance()->GetSubsystem<ULuaSubSystem>();
		if(LuaSubSystem && LuaSubSystem->MainStateWrapper.IsValid())
		{
			for(auto const & Item : LuaSubSystem->MainStateWrapper->GameWorldToLuaThread)
			{
				if(Item.GameWorld.Get() == InWorld)
				{
					return Item.TheState;
				}
			}
		}
	}

	return nullptr;
}

void ULuaSubSystem::StartupLua(UObject* InWorldContext,FString const & InStartupLuaFilePath)
{
	if(InWorldContext && InWorldContext->GetWorld() && InWorldContext->GetWorld()->GetGameInstance())
	{
		ULuaSubSystem * LuaSubSystem = InWorldContext->GetWorld()->GetGameInstance()->GetSubsystem<ULuaSubSystem>();
		if(LuaSubSystem)
		{
			LuaSubSystem->StartupLua(InStartupLuaFilePath);
		}
	}
}

void ULuaSubSystem::Deinitialize()
{
	UE_LOG(LuaSubsystem,Log,TEXT("LuaSubSystem::Deinitialize"));
	
	if(MainStateWrapper.IsValid())
	{
		FGPLuaGameplay::Get().OnLuaSubSystemDeinitialize();
		FGMMessageHelper::UnListenMessage("OnGameModeCreated", MainStateWrapper->GameIns.Get());
		if(NS_SLUA::lua_State * inL = MainStateWrapper->TheSLuaState.getLuaState())
		{
			if(MainStateWrapper->WorldRef != LUA_NOREF)
			{
				NS_SLUA::luaL_unref(inL,LUA_REGISTRYINDEX,MainStateWrapper->WorldRef);
				NS_SLUA::lua_pushnil(inL);
				NS_SLUA::lua_setglobal(inL,"GLuaWorld");
			}
			ULuaSubSystem::OnLuaStateCloseCallback.Broadcast(inL);
		}
		
		MainStateWrapper->TheSLuaState.close();
		LuaState2GameInstance.Remove(&MainStateWrapper->TheSLuaState);
	}
}


void ULuaSubSystem::StartupLua(FString const & InStartupLuaFilePath)
{
	UE_LOG(LuaSubsystem,Log,TEXT("CreateMainLuaState"));
	if(MainStateWrapper.IsValid() && !MainStateWrapper->IsValid)
	{
		MainStateWrapper->TheSLuaState.onInitEvent.AddUObject(this, &ULuaSubSystem::LuaStateInitCallback);
		MainStateWrapper->WorldRef = LUA_NOREF;
		MainStateWrapper->TheSLuaState.init();
		MainStateWrapper->IsValid = true;

		//
		
		if(!InStartupLuaFilePath.IsEmpty())
		{
			MainStateWrapper->TheSLuaState.doFile(TCHAR_TO_UTF8(*InStartupLuaFilePath));
		}
	}	
}

void ULuaSubSystem::LuaStateInitCallback()
{
	USING_NAMESPACE_NS_SLUA
	lua_State* inL = MainStateWrapper->TheSLuaState.getLuaState();

	if (inL)
	{
		LuaAutoRegistryClass::reg(inL);

		if (MainStateWrapper->GameIns.IsValid())
		{
			MainStateWrapper->TheSLuaState.attach(MainStateWrapper->GameIns.Get());
		}
		
		MainStateWrapper->TimerManager = MakeShareable(new FLuaTimerManager());
		MainStateWrapper->TimerManager->Open(inL);
		
		// global 
		SetupGlobalVariable();
		CreateLuaWorld(MainStateWrapper->GameIns->GetWorld());

		OnLuaStateInitCallback.Broadcast(inL);
		
		MainStateWrapper->TheSLuaState.doFile("main");
		MainStateWrapper->TheSLuaState.call("main");
		LuaState2GameInstance.Add(&MainStateWrapper->TheSLuaState, MainStateWrapper->GameIns);
	}
}


void ULuaSubSystem::SetupGlobalVariable()
{
	USING_NAMESPACE_NS_SLUA
	if (!MainStateWrapper.IsValid())
	{
		return;
	}

	lua_State* inL = MainStateWrapper->TheSLuaState.getLuaState();
	if (!inL)
	{
		return;
	}

#if WITH_EDITOR
	lua_pushnumber(inL, 1);
#else 
	lua_pushnumber(inL, 0);
#endif
	lua_setglobal(inL, "_WITH_EDITOR");

	lua_pushnumber(inL, 1);
#if PLATFORM_WINDOWS
	lua_setglobal(inL, "PLATFORM_WINDOWS");
#elif PLATFORM_ANDROID
	lua_setglobal(inL, "PLATFORM_ANDROID");
#elif PLATFORM_IOS
	lua_setglobal(inL, "PLATFORM_IOS");
#else 
	lua_pop(inL, 1);
#endif

	lua_createtable(inL, 0, 0);
	lua_pushvalue(inL,-1);
	MainStateWrapper->WorldRef = luaL_ref(inL, LUA_REGISTRYINDEX);
	lua_setglobal(inL,"GLuaWorld");
	
}

void ULuaSubSystem::CreateLuaWorld(UWorld* InWorld)
{
	if (!MainStateWrapper.IsValid())
	{
		return;
	}
	const ULuaSetting * LuaSetting = GetDefault<ULuaSetting>();
	if(LuaSetting == nullptr)
	{
		return;
	}
	for(FLuaGameWorldWrapper const & Item :MainStateWrapper->GameWorldToLuaThread)
	{
		if(Item.GameWorld.Get() == InWorld)
		{
			return;
		}
	}
	FString WorldPathName = InWorld->GetPathName();
	UE_LOG(LuaSubsystem,Log,TEXT("Create World Lua State for MapName %s"),*WorldPathName);
	NS_SLUA::lua_State* inL = MainStateWrapper->TheSLuaState.getLuaState();
	if (inL)
	{
		{
			ensure(MainStateWrapper->WorldRef != -1);
			NS_SLUA::lua_rawgeti(inL,LUA_REGISTRYINDEX,MainStateWrapper->WorldRef);
			NS_SLUA::lua_pushstring(inL,"__world");
			NS_SLUA::LuaObject::push(inL,InWorld,true);
			NS_SLUA::lua_rawset(inL,-3);
			lua_pop(inL,1);
			
		}
		{
			FLuaGameWorldWrapper & LuaWorld = MainStateWrapper->GameWorldToLuaThread.Emplace_GetRef();
			LuaWorld.GameWorld = InWorld;
			NS_SLUA::lua_State* WorldLuaState = NS_SLUA::lua_newthread(inL);
			if (WorldLuaState)
			{
				LuaWorld.LuaThreadRef = MainStateWrapper->TheSLuaState.addThread(WorldLuaState);
				LuaWorld.TheState = WorldLuaState;
			}
			lua_pop(inL,1);
		}
	}
}

void ULuaSubSystem::DestroyLuaWorld(UWorld* InWorld)
{
	if (!MainStateWrapper.IsValid())
	{
		return;
	}
	NS_SLUA::lua_State* inL = MainStateWrapper->TheSLuaState.getLuaState();
	if (inL)
	{
		for(FLuaGameWorldWrapper & Item : MainStateWrapper->GameWorldToLuaThread)
		{
			if(Item.GameWorld.Get())
			{
				if(Item.GameWorld.Get() == InWorld)
				{
					NS_SLUA::luaL_unref(inL, LUA_REGISTRYINDEX, Item.LuaThreadRef);
					Item.LuaThreadRef = LUA_NOREF;
					Item.TheState = nullptr;
					Item.GameWorld.Reset();
				}
			}
		}
	}

	MainStateWrapper->GameWorldToLuaThread.RemoveAll([](FLuaGameWorldWrapper const & Item)
	{
		return Item.LuaThreadRef == LUA_NOREF;
	});
}

