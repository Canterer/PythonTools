#include "LuaFileTagHelper/LuaFileTagHelper.h"
#include "LuaFileTagHelper/LuaFileTagCustomization.h"
#include "LuaFileTagHelper/LuaFileLog.h"
#include "Interfaces/IPluginManager.h"
#include "LuaFileTagNode.h"
#include "LuaSetting.h"
#include "ModuleManager.h"
#include "PlatformFilemanager.h"
#include "GenericPlatform/GenericPlatformFile.h"
#include "Misc/CoreDelegates.h"
#include "PropertyEditorModule.h"
FLuaFileTagModule::FOnRefresh FLuaFileTagModule::OnRefreshEvent;


void FLuaFileTagModule::StartupModule()
{
	FCoreDelegates::OnPostEngineInit.AddRaw(this, &FLuaFileTagModule::OnPostEngineInit);

	FLuaFileTagModule::OnRefreshEvent.BindRaw(this,&FLuaFileTagModule::ScanLuaFile);
	ScanLuaFile();
}

void FLuaFileTagModule::OnPostEngineInit()
{
	FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
	PropertyModule.RegisterCustomPropertyTypeLayout("LuaFileTag", 
		FOnGetPropertyTypeCustomizationInstance::CreateRaw(this,&FLuaFileTagModule::MakeInstance));
}

TSharedRef<class IPropertyTypeCustomization> FLuaFileTagModule::MakeInstance()
{
	return FLuaFileTagHelper::MakeInstance(LuaTagNodes);
}

void FLuaFileTagModule::ScanLuaFile()
{
	LuaSourceFileDirPath = FPaths::ProjectContentDir();
	LuaSourceFileDirPath = FPaths::Combine(LuaSourceFileDirPath,TEXT("LuaSource"));
	
	ULuaEditorSetting const * LuaEditorSetting = GetDefault<ULuaEditorSetting>();
	if(LuaEditorSetting && !LuaEditorSetting->LuaSourceRootDirInEditor.Path.IsEmpty())
	{
		LuaSourceFileDirPath = LuaEditorSetting->LuaSourceRootDirInEditor.Path;
	}
	

	UE_LOG(LogFileTagHelper,Log,TEXT("Find Lua Source FilePath %s"),*LuaSourceFileDirPath);
	
	TArray<FString> LuaSourceFilePaths;
	
	FPlatformFileManager::Get().GetPlatformFile().FindFilesRecursively(LuaSourceFilePaths,*FPaths::Combine(LuaSourceFileDirPath,TEXT("frontend")),TEXT(".lua"));

	FPlatformFileManager::Get().GetPlatformFile().FindFilesRecursively(LuaSourceFilePaths,*FPaths::Combine(LuaSourceFileDirPath,TEXT("game")),TEXT(".lua"));
	
	FPlatformFileManager::Get().GetPlatformFile().FindFilesRecursively(LuaSourceFilePaths,*FPaths::Combine(LuaSourceFileDirPath,TEXT("core")),TEXT(".lua"));

	LuaTagNodes.Empty();


	TArray<TSharedPtr<FLuaFileTagNode>> ChildNodes;
	for(FString & Item : LuaSourceFilePaths)
	{
		Item.RemoveFromStart(LuaSourceFileDirPath);
		Item.RemoveFromEnd(TEXT(".lua"));
		Item.RemoveFromStart(TEXT("/"));
		Item.ReplaceInline(TEXT("/"),TEXT("."));
	}

	for(FString const & Item : LuaSourceFilePaths)
	{
		TSharedPtr<FLuaFileTagNode> ItemTagNode = MakeShareable(new FLuaFileTagNode(Item));
		if (ItemTagNode->IsRootNode())
		{
			LuaTagNodes.Add(ItemTagNode);
		}
		else
		{
			ChildNodes.Add(ItemTagNode);
		}
	}

	for(TSharedPtr<FLuaFileTagNode> Item:ChildNodes)
	{
		FString RootNodeName = Item->GetRootNodeName();
		bool bFoundRootNode = false;
		TSharedPtr<FLuaFileTagNode> CurrentParentNode = nullptr;
		// search root node
		for(TSharedPtr<FLuaFileTagNode> RootNodeItem : LuaTagNodes)
		{
			if(RootNodeItem->MatchName(RootNodeName))
			{
				bFoundRootNode = true;
				CurrentParentNode = RootNodeItem;
			}
		}
		// if not found
		if(!bFoundRootNode)
		{
			TSharedPtr<FLuaFileTagNode> ItemTagNode = MakeShareable(new FLuaFileTagNode(RootNodeName));
			ItemTagNode->MakeCanSelected(false);
			CurrentParentNode = ItemTagNode;
			LuaTagNodes.Add(CurrentParentNode);
		}
		// from root node 
		FString ChildNodeName = Item->GetNodeName();
		TArray<FString> AllChildNodeName;
		ChildNodeName.ParseIntoArray(AllChildNodeName, TEXT("."));

		FString CurrentChildNodeName = RootNodeName;

		for (int32 i = 1; i < AllChildNodeName.Num() - 1; ++i)
		{
			CurrentChildNodeName = CurrentChildNodeName + TEXT(".") + AllChildNodeName[i];
			if (!CurrentParentNode->HasChild(CurrentChildNodeName))
			{
				TSharedPtr<FLuaFileTagNode> ItemTagNode = MakeShareable(new FLuaFileTagNode(CurrentChildNodeName));
				ItemTagNode->MakeCanSelected(false);
				CurrentParentNode->AddChild(ItemTagNode);
			}
			CurrentParentNode = CurrentParentNode->FindChildByName(CurrentChildNodeName);
		}

		CurrentParentNode->AddChild(Item);
	}

}
