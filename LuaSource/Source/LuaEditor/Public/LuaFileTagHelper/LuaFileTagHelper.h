#pragma once
#include "CoreMinimal.h"

#include "LuaFileTagHelper/LuaFileTagNode.h"

class FLuaFileTagModule
{
public:

	DECLARE_DELEGATE(FOnRefresh)
	static FOnRefresh OnRefreshEvent;
    void StartupModule();
	TSharedRef<class IPropertyTypeCustomization> MakeInstance();
private:
	void OnPostEngineInit();

	void ScanLuaFile();
	
private:
	FString LuaSourceFileDirPath;
	TArray<TSharedPtr<FLuaFileTagNode>> LuaTagNodes;


};
