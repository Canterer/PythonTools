#pragma once
#include "Modules/ModuleManager.h"
class FLuaFileTagModule;

class FLuaEditorModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule();
	virtual void ShutdownModule();
private:
	void OnPrePIEEnded(const bool NoUse);
private:
	TSharedPtr<FLuaFileTagModule> LuaFileTagModule;
};
