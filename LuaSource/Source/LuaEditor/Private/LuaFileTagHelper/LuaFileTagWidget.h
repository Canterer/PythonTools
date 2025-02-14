#pragma once

#include "Widgets/SCompoundWidget.h"
#include "LuaFileTagNode.h"
#include "STreeView.h"
#include "Templates/SharedPointer.h"
#include "Widgets/Input/SSearchBox.h"


DECLARE_DELEGATE_OneParam(FOnSelectedTagChange,FString);

class SLuaFileTagWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SLuaFileTagWidget)
		:_LuaFileRootNode(nullptr)
	{}
	SLATE_ARGUMENT(TArray<TSharedPtr<FLuaFileTagNode>> * ,LuaFileRootNode )

	SLATE_ARGUMENT(FString,CurrentSelectedTag)

	SLATE_EVENT(FOnSelectedTagChange,OnSelectedChanged)

	SLATE_END_ARGS()
public:
	void Construct(const FArguments& InArgs);
private:
	TSharedRef<ITableRow> OnGenerateRow(TSharedPtr<FLuaFileTagNode> InItem, const TSharedRef<STableViewBase>& OwnerTable);
	void OnGetChildren(TSharedPtr<FLuaFileTagNode> InItem, TArray< TSharedPtr<FLuaFileTagNode> >& OutChildren);
	void OnFilterTextChanged( const FText& InFilterText );
	ECheckBoxState IsTagChecked(TSharedPtr<FLuaFileTagNode> InItem) const;
	void OnTagCheckStatusChanged(ECheckBoxState NewCheckState, TSharedPtr<FLuaFileTagNode> NodeChanged);

	bool FilterTagRecursively(TSharedPtr<FLuaFileTagNode> const & InItem) const;
	FReply OnRefreshBtnClick() ;

	FReply ToggleAllTreeItemExpansion();
	void SetTreeItemAndChildrenExpansion(TSharedPtr<FLuaFileTagNode> const & InItem,bool bExpansion);
private:
	TArray< TSharedPtr<FLuaFileTagNode> > * LuaFileRootTags;

	TArray< TSharedPtr<FLuaFileTagNode> > FilterLuaFileTags;

	TSharedPtr<SSearchBox> SearchTagBox;
	TSharedPtr<class STreeView< TSharedPtr<FLuaFileTagNode> > > TagTreeWidget;

	FString CurrentSelectedTag;
	FOnSelectedTagChange OnSelectedChanged;

	FString CurrentFilterText;
	bool bExpandAllTreeItem;
};
