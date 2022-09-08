#pragma once
#include "CoreMinimal.h"

#include "EditorUndoClient.h"
#include "Widgets/SWidget.h"
#include "IPropertyTypeCustomization.h"
#include "Widgets/Input/SComboButton.h"
#include "Widgets/Views/STreeView.h"
#include "LuaFileTagHelper/LuaFileTagWidget.h"


class FLuaFileTagCustomization : public IPropertyTypeCustomization
{
public:
	FLuaFileTagCustomization(TArray<TSharedPtr<FLuaFileTagNode>> & InArray);
	~FLuaFileTagCustomization();

	/** Overridden to show an edit button to launch the message tag editor */
	virtual void CustomizeHeader(TSharedRef<class IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;

	/** Overridden to do nothing */
	virtual void CustomizeChildren(TSharedRef<IPropertyHandle> InStructPropertyHandle, class IDetailChildrenBuilder& ChildBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils) override {}


protected:
	TSharedRef<SWidget> GetListContent();

	void OnPropertyValueChanged();
	FText ShowSelectedTagName() const;
	void OnTagDoubleClicked();

	void OnSelectedTagChangedFromListView(FString InTag);
	void RefreshValueFromHandle();
private:
	TSharedPtr<SComboButton> EditButton;
	TSharedPtr<SLuaFileTagWidget> TagWidget;

	TArray<TSharedPtr<FLuaFileTagNode>> & LuaFileRootNodes;

	TSharedPtr<class IPropertyHandle> StructPropertyHandle;
	FString CurrentSelectedTagName;
};

class FLuaFileTagHelper
{
public:
	static TSharedRef<IPropertyTypeCustomization> MakeInstance(TArray<TSharedPtr<FLuaFileTagNode>>& InArray);
};


