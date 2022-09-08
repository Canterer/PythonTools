#include "LuaEditorModule.h"
#include "CoreMinimal.h"
#include "Editor.h"
#include "LuaFileTagHelper/LuaFileTagHelper.h"
#include "LuaRuntimeModule.h"
#include "ISettingsModule.h"
#include "LuaSetting.h"
#define LOCTEXT_NAMESPACE "LuaEditor"

void FLuaEditorModule::StartupModule()
{
	LuaFileTagModule = MakeShareable(new FLuaFileTagModule());
	LuaFileTagModule->StartupModule();

	if (auto SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		SettingsModule->RegisterSettings("Project", "LuaSetting", "Editor Settings",
            FText::FromString(TEXT("Editor Settings")),
            FText::FromString(TEXT("Editor Settings")),
            ULuaEditorSetting::StaticClass()->GetDefaultObject());
		
		SettingsModule->RegisterSettings("Project", "LuaSetting", "Game Settings",
			FText::FromString(TEXT("Game Settings")),
			FText::FromString(TEXT("Game Settings")),
			ULuaSetting::StaticClass()->GetDefaultObject());
	}
}
void FLuaEditorModule::ShutdownModule()
{
	if (auto SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		SettingsModule->UnregisterSettings("Project", "LuaSetting", "Game Settings");
		SettingsModule->UnregisterSettings("Project", "LuaSetting", "Editor Settings");
	}
}

void FLuaEditorModule::OnPrePIEEnded(const bool NoUse)
{
	
}

IMPLEMENT_MODULE(FLuaEditorModule,LuaEditor)

#undef LOCTEXT_NAMESPACE
