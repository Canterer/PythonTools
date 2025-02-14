#include "LuaFileTagWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Input/SCheckBox.h"
#include "EditorStyleSet.h"
#include "LuaFileTagHelper/LuaFileTagHelper.h"


#define LOCTEXT_NAMESPACE "SLuaFileTagWidget"

void SLuaFileTagWidget::Construct(const FArguments& InArgs)
{
	bExpandAllTreeItem = false;
	LuaFileRootTags = InArgs._LuaFileRootNode;

	CurrentSelectedTag = InArgs._CurrentSelectedTag;

	OnSelectedChanged = InArgs._OnSelectedChanged;

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FEditorStyle::GetBrush("ToolPanel.GroupBorder"))
		[
			SNew(SVerticalBox)

			+SVerticalBox::Slot()
			.VAlign(VAlign_Top)
			.AutoHeight()
			[
				SNew(SHorizontalBox)
				+SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SButton)
					.OnClicked(this,&SLuaFileTagWidget::OnRefreshBtnClick)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("SLuaFileTagWidget_Refresh", "Refresh"))
					]
				]
				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SButton)
					.OnClicked(this, &SLuaFileTagWidget::ToggleAllTreeItemExpansion)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("SLuaFileTagWidget_ExpandAll", "Expand All"))
					]
				]
				+SHorizontalBox::Slot()
				.FillWidth(1)
				[
					SAssignNew(SearchTagBox, SSearchBox)
					.HintText(LOCTEXT("SLuaFileTagWidget_SearchLuaFiles", "Search lua files"))
					.OnTextChanged(this, &SLuaFileTagWidget::OnFilterTextChanged)
				]
			]
			+SVerticalBox::Slot()
			.FillHeight(1)
			.Padding(4.0f, 0.0f)
			[
				SNew(SBorder)
				.Padding(4.0f)
				[
					SAssignNew(TagTreeWidget,STreeView<TSharedPtr<FLuaFileTagNode> >)

					.TreeItemsSource(LuaFileRootTags)
					.OnGenerateRow(this, &SLuaFileTagWidget::OnGenerateRow)
					.OnGetChildren(this, &SLuaFileTagWidget::OnGetChildren)
					.SelectionMode(ESelectionMode::Single)
					
				]
				
			]

		]
	];

	for(TSharedPtr<FLuaFileTagNode> const & Item: *LuaFileRootTags )
	{
		TagTreeWidget->SetItemExpansion(Item,true);
	}
	
}

void SLuaFileTagWidget::OnFilterTextChanged( const FText& InFilterText )
{
	CurrentFilterText = InFilterText.ToString();
	if(InFilterText.IsEmpty())
	{
		TagTreeWidget->SetTreeItemsSource(LuaFileRootTags);
	}
	else
	{
		FilterLuaFileTags.Empty();
		for(TSharedPtr<FLuaFileTagNode> const & Item : *LuaFileRootTags)
		{
			if(FilterTagRecursively(Item))
			{
				FilterLuaFileTags.Add(Item);
			}
		}

		TagTreeWidget->SetTreeItemsSource(&FilterLuaFileTags);
	}
	TagTreeWidget->RequestTreeRefresh();
}

TSharedRef<ITableRow> SLuaFileTagWidget::OnGenerateRow(TSharedPtr<FLuaFileTagNode> InItem, const TSharedRef<STableViewBase>& OwnerTable)
{
	return SNew(STableRow< TSharedPtr<FLuaFileTagNode> >, OwnerTable)
		.Style(FEditorStyle::Get(), "Game","playTagTreeView")
		[
			SNew(SCheckBox)
			.IsEnabled(InItem->CanSelected())
			.OnCheckStateChanged(this, &SLuaFileTagWidget::OnTagCheckStatusChanged, InItem)
			.IsChecked(this, &SLuaFileTagWidget::IsTagChecked, InItem)
			[
				SNew(STextBlock)
				.Text(FText::FromString(InItem->GetTagName()))
			]
			
		];

}

void SLuaFileTagWidget::OnGetChildren(TSharedPtr<FLuaFileTagNode> InItem, TArray< TSharedPtr<FLuaFileTagNode> >& OutChildren)
{
	if(CurrentFilterText.Len() == 0)
	{
		InItem->FindAllChilds(OutChildren);
	}
	else
	{
		OutChildren.Empty();

		TArray< TSharedPtr<FLuaFileTagNode> > ItemChilds;
		InItem->FindAllChilds(ItemChilds);

		for(TSharedPtr<FLuaFileTagNode> const & Item:ItemChilds)
		{
			if(FilterTagRecursively(Item))
			{
				OutChildren.Add(Item);
			}
		}
	}
	
}

ECheckBoxState SLuaFileTagWidget::IsTagChecked(TSharedPtr<FLuaFileTagNode> InItem) const
{
	if(CurrentSelectedTag.Equals(InItem->GetNodeName()))
	{
		return ECheckBoxState::Checked;
	}
	return ECheckBoxState::Unchecked;
}

void SLuaFileTagWidget::OnTagCheckStatusChanged(ECheckBoxState NewCheckState, TSharedPtr<FLuaFileTagNode> InItem)
{
	if (NewCheckState == ECheckBoxState::Checked)
	{
		CurrentSelectedTag = InItem->GetNodeName();
	}
	else if(NewCheckState == ECheckBoxState::Unchecked)
	{
		CurrentSelectedTag = TEXT("");
	}

	OnSelectedChanged.ExecuteIfBound(CurrentSelectedTag);
}

bool SLuaFileTagWidget::FilterTagRecursively(TSharedPtr<FLuaFileTagNode> const & InItem) const
{
	if(InItem->GetNodeName().Contains(CurrentFilterText))
	{
		return true;
	}
	if(InItem->GetChildNum() == 0)
	{
		return false;	
	}
	
	for (TSharedPtr<FLuaFileTagNode> const& ChildItem : InItem->GetChilds())
	{
		if(FilterTagRecursively(ChildItem))
		{
			return true;
		}
	}

	return false;
}

FReply SLuaFileTagWidget::OnRefreshBtnClick()
{
	FLuaFileTagModule::OnRefreshEvent.ExecuteIfBound();
	
	SearchTagBox->SetText(FText::GetEmpty());
	CurrentFilterText = TEXT("");
	TagTreeWidget->RequestTreeRefresh();
	return FReply::Handled();
}

FReply SLuaFileTagWidget::ToggleAllTreeItemExpansion()
{
	

	if(CurrentFilterText.Len() == 0)
	{
		bExpandAllTreeItem = !bExpandAllTreeItem;

		for(TSharedPtr<FLuaFileTagNode> const & Item: *LuaFileRootTags )
		{
			TArray< TSharedPtr<FLuaFileTagNode> > OutChildren;
			OnGetChildren(Item,OutChildren);

			for (TSharedPtr<FLuaFileTagNode> const& ChildItem : OutChildren)
			{
				SetTreeItemAndChildrenExpansion(ChildItem, bExpandAllTreeItem);
			}
		}
	}
	else
	{
		if(FilterLuaFileTags.Num() > 0)
		{
			bExpandAllTreeItem = !bExpandAllTreeItem;

			for (TSharedPtr<FLuaFileTagNode> const& Item : FilterLuaFileTags)
			{
				TArray< TSharedPtr<FLuaFileTagNode> > OutChildren;
				OnGetChildren(Item,OutChildren);
				
				for (TSharedPtr<FLuaFileTagNode> const& ChildItem : OutChildren)
				{
					SetTreeItemAndChildrenExpansion(ChildItem, bExpandAllTreeItem);
				}
			}
		}		
	}

	return FReply::Handled();
}
void SLuaFileTagWidget::SetTreeItemAndChildrenExpansion(TSharedPtr<FLuaFileTagNode> const & InItem,bool bExpansion)
{
	TagTreeWidget->SetItemExpansion(InItem, bExpansion);

	TArray< TSharedPtr<FLuaFileTagNode> > OutChildren;

	
	OnGetChildren(InItem,OutChildren);

	for (TSharedPtr<FLuaFileTagNode> const& ChildItem : OutChildren)
	{
		SetTreeItemAndChildrenExpansion(ChildItem, bExpansion);
	}

}

#undef LOCTEXT_NAMESPACE
