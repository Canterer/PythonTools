// Copyright Epic Games, Inc. All Rights Reserved.

#include "CheckDataGraph.h"
#include "CheckDataGraphStyle.h"
#include "CheckDataGraphCommands.h"
#include "LevelEditor.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"

#include "SCheckDataGraphWindow.h"

static const FName CheckDataGraphTabName("CheckDataGraph");

#define LOCTEXT_NAMESPACE "FCheckDataGraphModule"

void FCheckDataGraphModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	
	FCheckDataGraphStyle::Initialize();
	FCheckDataGraphStyle::ReloadTextures();

	FCheckDataGraphCommands::Register();
	
	PluginCommands = MakeShareable(new FUICommandList);

	PluginCommands->MapAction(
		FCheckDataGraphCommands::Get().OpenPluginWindow,
		FExecuteAction::CreateRaw(this, &FCheckDataGraphModule::PluginButtonClicked),
		FCanExecuteAction());

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FCheckDataGraphModule::RegisterMenus));
	
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(CheckDataGraphTabName, FOnSpawnTab::CreateRaw(this, &FCheckDataGraphModule::OnSpawnPluginTab))
		.SetDisplayName(LOCTEXT("FCheckDataGraphTabTitle", "CheckDataGraph"))
		.SetMenuType(ETabSpawnerMenuType::Hidden);
}

void FCheckDataGraphModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FCheckDataGraphStyle::Shutdown();

	FCheckDataGraphCommands::Unregister();

	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(CheckDataGraphTabName);
}

TSharedRef<SDockTab> FCheckDataGraphModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
	FText WidgetText = FText::Format(
		LOCTEXT("WindowWidgetText", "Add code to {0} in {1} to override this window's contents"),
		FText::FromString(TEXT("FCheckDataGraphModule::OnSpawnPluginTab")),
		FText::FromString(TEXT("CheckDataGraph.cpp"))
		);

	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			// Put your tab content here!
			/*SNew(SBox)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(WidgetText)
			]*/
			SNew(SCheckDataGraphWindow)
		];
}

void FCheckDataGraphModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(CheckDataGraphTabName);
}

void FCheckDataGraphModule::RegisterMenus()
{
	// Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
	FToolMenuOwnerScoped OwnerScoped(this);

	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
		{
			FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
			Section.AddMenuEntryWithCommandList(FCheckDataGraphCommands::Get().OpenPluginWindow, PluginCommands);
		}
	}

	{
		UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
		{
			FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("Settings");
			{
				FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FCheckDataGraphCommands::Get().OpenPluginWindow));
				Entry.SetCommandList(PluginCommands);
			}
		}
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FCheckDataGraphModule, CheckDataGraph)