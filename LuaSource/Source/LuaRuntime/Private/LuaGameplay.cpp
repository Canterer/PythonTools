#include "LuaGameplay.h"

#include "LuaAsyncLoader.h"
#include "LuaGameplayTimer.h"
#include "LuaSubsystem.h"

USING_NAMESPACE_NS_SLUA

static TMap<void*, NS_SLUA::LuaVar> LuaTables;
	
#define Ex_LuaHook (EX_Max-1)

#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
extern uint8 GRegisterNative(int32 NativeBytecodeIndex, const FNativeFuncPtr& Func);
#else
extern uint8 GRegisterNative(int32 NativeBytecodeIndex, const Native& Func);
#endif

#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
DEFINE_FUNCTION(_luaOverrideFunc)
#else
void _luaOverrideFunc(FFrame& Stack, RESULT_DECL)
#endif
{
	USING_NAMESPACE_NS_SLUA
	UFunction* func = Stack.Node;
	ensure(func);
	UObject* lb = Stack.Object;//checkBase(Stack.Object);

	if (!lb) {
		*(bool*)RESULT_PARAM = false;
		return;
	}

	ensure(lb);

	void* params = Stack.Locals;

	NS_SLUA::LuaVar* luaSelfTablePtr = LuaTables.Find(lb);
	if(!luaSelfTablePtr)
	{
		*(bool*)RESULT_PARAM = false;
		return;
	}
	NS_SLUA::LuaVar luaSelfTable = *luaSelfTablePtr;
	if(!luaSelfTable.isTable())
	{
		*(bool*)RESULT_PARAM = false;
		return;
	}
	NS_SLUA::LuaVar lfunc = luaSelfTable.getFromTable<NS_SLUA::LuaVar>(func->GetName(), true);
	if(lfunc.isFunction())
	{
		lfunc.callByUFunction(func, (uint8*)params, Stack.OutParms, nullptr, luaSelfTablePtr);
		*(bool*)RESULT_PARAM = true;
		return;
	}
	*(bool*)RESULT_PARAM = false;
}

int FGPLuaGameplay::__indexCppInstance(NS_SLUA::lua_State* L)
{
	USING_NAMESPACE_NS_SLUA
	lua_pushstring(L, SLUA_CPPINST);
	lua_rawget(L, 1);
	void* ud = lua_touserdata(L, -1);
	if (!ud)
		luaL_error(L, "expect LuaBase table at arg 1");
	lua_pop(L, 1);
	UObject* obj = (UObject*)ud;
	if (!NS_SLUA::LuaObject::isUObjectValid(obj))
	{
		return 0;
	}
	LuaObject::push(L, obj, true);

	// push key
	lua_pushvalue(L, 2);
	// get field from real actor
	lua_gettable(L, -2);
	return 1;
}

int FGPLuaGameplay::__trySetCppInstance(NS_SLUA::lua_State* L) {
	// set field to obj, may raise an error
	lua_settable(L, 1);
	return 0;
}

int FGPLuaGameplay::__newindexCppInstance(NS_SLUA::lua_State* L)
{
	USING_NAMESPACE_NS_SLUA
	lua_pushstring(L, SLUA_CPPINST);
	lua_rawget(L, 1);
	void* ud = lua_touserdata(L, -1);
	if (!ud)
		luaL_error(L, "expect LuaBase table at arg 1");
	lua_pop(L, 1);
	LuaObject::push(L, (UObject*)ud, false);

	lua_pushcfunction(L, FGPLuaGameplay::__trySetCppInstance);
	// push cpp inst
	lua_pushvalue(L, -2);
	// push key
	lua_pushvalue(L, 2);
	// push value
	lua_pushvalue(L, 3);
	// set ok?
	if (lua_pcall(L, 3, 0, 0)) {
		lua_pop(L, 1);
		// push key
		lua_pushvalue(L, 2);
		// push value
		lua_pushvalue(L, 3);
		// rawset to table
		lua_rawset(L, 1);
	}
	return 0;
}


#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
void FGPLuaGameplay::hookBpScript(UFunction* func, FNativeFuncPtr hookfunc) {
#else
void FGPLuaGameplay::hookBpScript(UFunction * func, Native hookfunc)
{
	#endif
	if (!LuaBase::regExCode) {
		GRegisterNative(Ex_LuaHook, hookfunc);
		LuaBase::regExCode = true;
	}
	// if func had hooked
	if (func->Script.Num() > 5 && func->Script[5] == Ex_LuaHook)
		return;
	uint8 code[] = { EX_JumpIfNot,8,0,0,0,Ex_LuaHook,EX_Return,EX_Nothing, EX_Return, EX_Nothing, EX_EndOfScript };
	func->Script.Insert(code, sizeof(code), 0);
}

void FGPLuaGameplay::_bindOverrideFunc(NS_SLUA::LuaVar luaTable,UObject * obj)
{
	ensure(obj && luaTable.isTable());
	UClass* cls = obj->GetClass();
	ensure(cls);
	
	EFunctionFlags availableFlag = FUNC_BlueprintEvent;
	for (TFieldIterator<UFunction> it(cls); it; ++it) {
		if (!(it->FunctionFlags & availableFlag))
			continue;
		if (luaTable.getFromTable<LuaVar>(it->GetName(), true).isFunction()) {
			#if ((ENGINE_MINOR_VERSION>18) && (ENGINE_MAJOR_VERSION>=4))
			FGPLuaGameplay::hookBpScript(*it, (FNativeFuncPtr)&_luaOverrideFunc);
			#else
			FGPLuaGameplay::hookBpScript(*it, (Native)&LuaBase::luaOverrideFunc);
			#endif
		}
	}
}

namespace LuaSuperNS
{
template<typename T>
UFunction* getSuperOrRpcFunction(lua_State* L) {
	CheckUD(T, L, 1);
	lua_getmetatable(L, 1);
	const char* name = LuaObject::checkValue<const char*>(L, 2);

	lua_getfield(L, -1, name);
	lua_remove(L, -2); // remove mt of ud
	if (!lua_isnil(L, -1)) {
		return nullptr;
	}

	UObject* obj = UD->base->getContext().Get();
	if (!obj)
		luaL_error(L, "Context is invalid");
	if (UD->base->getIndexFlag() == LuaBase::IF_RPC)
		luaL_error(L, "Can't call super in RPC function");

	UFunction* func = obj->GetClass()->FindFunctionByName(UTF8_TO_TCHAR(name));
	if (!func || (func->FunctionFlags&FUNC_BlueprintEvent) == 0)
		luaL_error(L, "Can't find function %s in super", name);

	return func;
}

int superOrRpcCall(lua_State* L,UFunction* func, UObject* obj)
{
	if (!obj) return 0;

	//NS_SLUA::NewObjectRecorder objectRecorder(L);

	uint8* params = (uint8*)FMemory_Alloca(func->ParmsSize);
	FMemory::Memzero(params, func->ParmsSize);
	for (TFieldIterator<UProperty> it(func); it && it->HasAnyPropertyFlags(CPF_Parm); ++it)
	{
		UProperty* localProp = *it;
		checkSlow(localProp);
		if (!localProp->HasAnyPropertyFlags(CPF_ZeroConstructor))
		{
			localProp->InitializeValue_InContainer(params);
		}
	}

	LuaObject::fillParam(L, 2, func, params);
	{
		// call function with params
		LuaObject::callUFunction(L, obj, func, params);
	}
	// return value to push lua stack
	int outParamCount = LuaObject::returnValue(L, func, params, nullptr);

	for (TFieldIterator<UProperty> it(func); it && (it->HasAnyPropertyFlags(CPF_Parm)); ++it)
	{
		it->DestroyValue_InContainer(params);
	}

	return outParamCount;
}

int __superCall(lua_State* L)
{
	CheckUD(UObject, L, 1);
	lua_pushvalue(L, lua_upvalueindex(1));
	UFunction* func = (UFunction*) lua_touserdata(L, -1);
	if (!func || !func->IsValidLowLevel())
		luaL_error(L, "Super function is isvalid");
	lua_pop(L, 1);
	int ret = superOrRpcCall(L, func, UD);
	return ret;
}

int __superIndex(lua_State* L) {
		
	UFunction* func = getSuperOrRpcFunction<LuaSuper>(L);
	if (!func) return 1;
		
	return LuaObject::push(L, func);

	//lua_pushlightuserdata(L, func);
	//lua_pushcclosure(L, __superCall, 1);
	//return 1;
}

int supermt(lua_State* L)
{
	//LuaObject::setupMTSelfSearch(L);
	RegMetaMethodByName(L, "__index", __superIndex);
	return 0;
}

template<typename T>
static int genericGC(lua_State* L) {
	CheckUDGC(T, L, 1);
	delete UD;
	return 0;
}

}

int FGPLuaGameplay::BindObject(lua_State* L)
{
	UObject* ParentCppObj = LuaObject::checkValue<UObject*>(L, 1);
	LuaVar ChildLuaTable(L, 2);
	if (!ChildLuaTable.isTable() ||!IsValid(ParentCppObj))
		return 0;
	ChildLuaTable.push(L);
	lua_pushlightuserdata(L, (void*)ParentCppObj);
	lua_setfield(L, -2, SLUA_CPPINST);

	// LuaObject::pushType(L, ParentCppObj , "LuaSuper", supermt, nullptr);
	// lua_setfield(L, -2, "CppSuper");

	FGPLuaGameplay::_bindOverrideFunc(ChildLuaTable, ParentCppObj);
	
	if(lua_getmetatable(L, -1) == 1 || luaL_newmetatable(L, "LuaBind") == 1)
	{
		lua_pushcfunction(L, __indexCppInstance);
		lua_setfield(L, -2, "__index");
		lua_pushcfunction(L, __newindexCppInstance);
		lua_setfield(L, -2, "__newindex");
	}
	lua_setmetatable(L, -2);
	LuaTables.Add(ParentCppObj, ChildLuaTable);
	return 0;
}

int FGPLuaGameplay::UnBindObject(lua_State* L)
{
	UObject* CppObj = LuaObject::checkValue<UObject*>(L, 1);
	LuaTables.Remove(CppObj);
	return 0;
}

int FGPLuaGameplay::RegisterComponent(lua_State* L)
{
	LuaVar ActorPtr(L, 1);
	UObject* OwnerActor = LuaObject::checkValue<UObject*>(L, 1);
	UClass* CompClass = LuaObject::checkValue<UClass*>(L, 2);
	LuaVar ObjName(L, 3);
	if (!IsValid(OwnerActor) || !IsValid(CompClass))
		return 0;
	UObject* NewObj = StaticConstructObject_Internal(CompClass, OwnerActor, ObjName.toString());

	UActorComponent* Comp = Cast<UActorComponent>(NewObj);
	Comp->RegisterComponent();

	LuaObject::push(L, NewObj);
	
	return 1;	
}

int FGPLuaGameplay::UnRegisterComponent(lua_State* L)
{
	UObject* OwnerActor = LuaObject::checkValue<UObject*>(L, 1);
	return 0;
}

void FGPLuaGameplay::OnLuaSubSystemInitialize(const UGameInstance* GameInstance)
{
	ULuaSubSystem::OnLuaStateInitCallback.AddRaw(this, &FGPLuaGameplay::OnLuaStateInit);
	ULuaSubSystem::OnLuaStateCloseCallback.AddRaw(this, &FGPLuaGameplay::OnLuaStateClose);
	
	// ULuaSubSystem::StartupLua(GameInstance->GetWorld(), "");
	return;
	if(cur_lua_state)
	{
		lua_pushcfunction(cur_lua_state, BindObject);
		lua_setglobal(cur_lua_state, "bind_object");
		
		lua_pushcfunction(cur_lua_state, UnBindObject);
		lua_setglobal(cur_lua_state, "unbind_object");
	
		lua_pushcfunction(cur_lua_state, RegisterComponent);
		lua_setglobal(cur_lua_state, "register_component");
		
		lua_pushcfunction(cur_lua_state, UnRegisterComponent);
		lua_setglobal(cur_lua_state, "unregister_component");

		LuaGameplayTimer::Open(cur_lua_state);
		LuaAsyncLoader::Open(cur_lua_state);
		
		LuaState* State = LuaState::get(cur_lua_state);
		InitTable = State->doFile("gameplay.init");
		if(!InitTable.isTable())
		{
			return;
		}
		TickFunc = InitTable.getFromTable<NS_SLUA::LuaVar>("run", true);
		if(!TickFunc.isFunction())
		{
			return;
		}
		FCoreDelegates::OnEndFrame.AddRaw(this, &FGPLuaGameplay::OnEngineTick);
	}
}

void FGPLuaGameplay::OnLuaSubSystemDeinitialize()
{
	FCoreDelegates::OnEndFrame.RemoveAll(this);
}

void FGPLuaGameplay::OnLuaStateInit(NS_SLUA::lua_State * inL)
{
	cur_lua_state = inL;
}

void FGPLuaGameplay::OnLuaStateClose(NS_SLUA::lua_State * inL)
{
	cur_lua_state = nullptr;
}

void FGPLuaGameplay::OnGameModeCreated(AGameModeBase* GameMode)
{
	if(!IsValid(GameMode) || !IsValid(GameMode->GetWorld()) || GameMode->GetWorld()->GetNetMode() != NM_Standalone)
	{
		return;
	}
	UGameInstance* GameInstance = GameMode->GetWorld()->GetGameInstance();

	if(!IsValid(GameInstance))
	{
		return;
	}

	OnLuaSubSystemInitialize(GameInstance);
	
	if(!InitTable.isTable())
	{
		return;
	}
	LuaVar Func = InitTable.getFromTable<NS_SLUA::LuaVar>("OnGameModeCreated", true);
	if(Func.isFunction())
	{
		Func.call(InitTable, GameMode);
	}
}

void FGPLuaGameplay::OnEngineTick() const
{
	const float DeltaTime = FApp::GetDeltaTime();
	TickFunc.call(InitTable, DeltaTime);	
}
