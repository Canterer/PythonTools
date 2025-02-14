
#include "LuaFileTagHelper/LuaFileTagCustomization.h"
#if WITH_EDITOR
#include "Editor.h"
#include "SNotificationList.h"
#include "NotificationManager.h"
#endif
#include "Widgets/SBoxPanel.h"
#include "Widgets/Input/SHyperlink.h"
#include "DetailWidgetRow.h"
#include "PropertyHandle.h"
#include "IPropertyTypeCustomization.h"
#include "LuaSetting.h"
#include "Components/SlateWrapperTypes.h"
#include "LuaFileSystem/LuaFileTag.h"


#define LOCTEXT_NAMESPACE "LuaFileTagCustomization"


TSharedRef<IPropertyTypeCustomization> FLuaFileTagHelper::MakeInstance(TArray<TSharedPtr<FLuaFileTagNode>> & InArray)
{
	return MakeShareable(new FLuaFileTagCustomization(InArray));
}

FLuaFileTagCustomization::FLuaFileTagCustomization(TArray<TSharedPtr<FLuaFileTagNode>> & InArray)
	:LuaFileRootNodes(InArray)
{
	
}

FLuaFileTagCustomization::~FLuaFileTagCustomization()
{
	EditButton.Reset();
	TagWidget.Reset();
	
}

void FLuaFileTagCustomization::CustomizeHeader(TSharedRef<class IPropertyHandle> InStructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
	StructPropertyHandle = InStructPropertyHandle;

	RefreshValueFromHandle();

	HeaderRow
		.NameContent()
		[
			InStructPropertyHandle->CreatePropertyNameWidget()
		]
		.ValueContent()
		.MaxDesiredWidth(512)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SAssignNew(EditButton, SComboButton)
				.OnGetMenuContent(this, &FLuaFileTagCustomization::GetListContent)
				//.OnMenuOpenChanged(this, &FMessageTagCustomization::OnMessageTagListMenuOpenStateChanged)
				.ContentPadding(FMargin(2.0f, 2.0f))
				.MenuPlacement(MenuPlacement_BelowAnchor)
				.ButtonContent()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("LuaFileTagCustomization", "Bind"))
				]
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SBorder)
				//.Visibility(this, &FMessageTagCustomization::GetVisibilityForTagTextBlockWidget, false)
				.Padding(4.0f)
				[
					SNew(SHyperlink)
					.Text(this, &FLuaFileTagCustomization::ShowSelectedTagName)
					.OnNavigate(this, &FLuaFileTagCustomization::OnTagDoubleClicked)
				]
			]
			
		];
}


TSharedRef<SWidget> FLuaFileTagCustomization::GetListContent()
{
	TagWidget = SNew(SLuaFileTagWidget)
		.LuaFileRootNode(&LuaFileRootNodes)
		.CurrentSelectedTag(CurrentSelectedTagName)
		.OnSelectedChanged(this,&FLuaFileTagCustomization::OnSelectedTagChangedFromListView);

	return SNew(SVerticalBox)
		.Visibility(EVisibility::SelfHitTestInvisible)
		+SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SBox)
			.Padding(3)
			[
				SNew(SHorizontalBox)
				+SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SButton)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("LuaFileTagCustomization_CreateFile","CreateFile"))
					]
				]
			]
		]
		+SVerticalBox::Slot()
		.FillHeight(4)
		.MaxHeight(600)
		[
			TagWidget.ToSharedRef()
		];
		
}

void FLuaFileTagCustomization::OnPropertyValueChanged()
{
	
	if (StructPropertyHandle.IsValid() && StructPropertyHandle->GetProperty())
	{
		TArray<void*> RawStructData;
		StructPropertyHandle->AccessRawData(RawStructData);
		if (RawStructData.Num() > 0)
		{
			FLuaFileTag* Tag = (FLuaFileTag*)(RawStructData[0]);
			
			if (Tag)
			{
				FString FormattedString = TEXT("(LuaFilePath=\"");
				FormattedString += CurrentSelectedTagName;
				FormattedString += TEXT("\")");

				StructPropertyHandle->SetValueFromFormattedString(FormattedString);
			}
			
		}

	}
}

FText FLuaFileTagCustomization::ShowSelectedTagName() const
{
	return FText::FromString(CurrentSelectedTagName);
}

void FLuaFileTagCustomization::OnTagDoubleClicked()
{
	ULuaEditorSetting const * LuaSetting = GetDefault<ULuaEditorSetting>();
	if(LuaSetting && !LuaSetting->LuaSourceRootDirInEditor.Path.IsEmpty() && !LuaSetting->FileEditorLocation.FilePath.IsEmpty())
	{
		FString LuaFilePath = CurrentSelectedTagName;
		LuaFilePath = LuaFilePath.Replace(TEXT("."),TEXT("\\"));
		LuaFilePath = LuaFilePath.Replace(TEXT("/"),TEXT("\\"));
		LuaFilePath = FPaths::ConvertRelativePathToFull(LuaSetting->LuaSourceRootDirInEditor.Path) / LuaFilePath + ".lua";

		if(FPaths::FileExists(LuaFilePath) && FPaths::FileExists(LuaSetting->FileEditorLocation.FilePath))
		{
			FProcHandle Proc = FPlatformProcess::CreateProc(*LuaSetting->FileEditorLocation.FilePath, *LuaFilePath, true, true, false, nullptr, 0, nullptr, nullptr);
			if (Proc.IsValid())
			{
				return;
			}
			else
			{
				#if WITH_EDITOR
				FNotificationInfo NotificationInfo(FText::FromString(TEXT("Create Proc Failer !!!")));
				FSlateNotificationManager::Get().AddNotification(NotificationInfo);
				#endif
				
				FPlatformProcess::CloseProc(Proc);
			}
		}

#if PLATFORM_WINDOWS
		LuaFilePath = FPaths::GetPath(LuaFilePath);
		while((!FPaths::DirectoryExists(LuaFilePath)) && LuaFilePath.Len() > 3)
		{
			LuaFilePath = FPaths::GetPath(LuaFilePath);
		}
		FPlatformProcess::ExploreFolder(*LuaFilePath);
#endif
	}
	else
	{
		#if WITH_EDITOR
		FNotificationInfo NotificationInfo(FText::FromString(TEXT("Open Editor Setting !!!")));
		FSlateNotificationManager::Get().AddNotification(NotificationInfo);
		#endif
	}
	
	//
}


void FLuaFileTagCustomization::OnSelectedTagChangedFromListView(FString InTag)
{
	CurrentSelectedTagName = InTag;

	OnPropertyValueChanged();
}

void FLuaFileTagCustomization::RefreshValueFromHandle()
{
	if (StructPropertyHandle.IsValid() && StructPropertyHandle->GetProperty())
	{
		TArray<void*> RawStructData;
		StructPropertyHandle->AccessRawData(RawStructData);
		if (RawStructData.Num() > 0)
		{
			FLuaFileTag* Tag = (FLuaFileTag*)(RawStructData[0]);
			if(Tag)
			{
				CurrentSelectedTagName = Tag->LuaFilePath;
			}
		}
	}
}



#undef LOCTEXT_NAMESPACE
