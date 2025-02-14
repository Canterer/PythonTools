#include "UserDefineClassMacro.h"


static TArray<NS_SLUA::lua_CFunction>* AutoRegistryClassFunc = nullptr;

LuaAutoRegistryClass::LuaAutoRegistryClass(NS_SLUA::lua_CFunction setup) {
	if (!AutoRegistryClassFunc) AutoRegistryClassFunc = new TArray<NS_SLUA::lua_CFunction>();
	AutoRegistryClassFunc->Add(setup);
}

void LuaAutoRegistryClass::reg(NS_SLUA::lua_State* L) {
	if (!AutoRegistryClassFunc)
		return;

	for (auto it : *AutoRegistryClassFunc)
		it(L);
}
