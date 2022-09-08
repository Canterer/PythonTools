#pragma once
#include "Templates/SharedPointer.h"

struct FLuaFileTagNode : public TSharedFromThis<FLuaFileTagNode>
{
public:
	FLuaFileTagNode(FString const & InLuaFileName)
	{
		LuaRequireName = InLuaFileName;
		bCanSelected = true;
	}

	void MakeCanSelected(bool InCanSelected)
	{
		bCanSelected = InCanSelected;
	}
	bool CanSelected()
	{
		return bCanSelected;
	}
	bool IsRootNode()
	{
		return !LuaRequireName.Contains(TEXT("."));
	}
	FString GetParentNodeName()
	{
		int32 LastDotIndex = -1;
		LuaRequireName.FindLastChar(TCHAR('.'),LastDotIndex);
		return LuaRequireName.Left(LastDotIndex);
	}
	FString GetRootNodeName()
	{
		FString RootNodeName = LuaRequireName;
		while(RootNodeName.Contains(TEXT(".")))
		{
			int32 LastDotIndex = -1;
			RootNodeName.FindLastChar(TCHAR('.'), LastDotIndex);
			RootNodeName = RootNodeName.Left(LastDotIndex);
		}
		return RootNodeName;
	}

	FString GetNodeName()
	{
		return LuaRequireName;
	}

	bool MatchName(FString const & InMatchName)
	{
		return LuaRequireName.Equals(InMatchName);
	}

	bool HasChild(FString const & InChildName)
	{
		for(TSharedPtr<FLuaFileTagNode> & Item:Childs)
		{
			if(Item->MatchName(InChildName))
			{
				return true;
			}
		}
		return false;
	}

	void AddChild(TSharedPtr<FLuaFileTagNode> InChild)
	{
		Childs.Add(InChild);
	}

	TSharedPtr<FLuaFileTagNode> FindChildByName(FString InChildName)
	{
		for (TSharedPtr<FLuaFileTagNode>& Item : Childs)
		{
			if (Item->MatchName(InChildName))
			{
				return Item;
			}
		}

		return nullptr;
	}

	FString GetTagName()
	{
		int32 LastDotIndex = -1;
		if(LuaRequireName.Contains(TEXT(".")))
		{
			LuaRequireName.FindLastChar(TCHAR('.'),LastDotIndex);
			FString TagName = LuaRequireName.RightChop(LastDotIndex + 1);
			return TagName;
		}
		return LuaRequireName;
	}

	void FindAllChilds(TArray<TSharedPtr<FLuaFileTagNode> > & OutAllChilds,FString const & InFilterText = TEXT(""))
	{
		for(TSharedPtr<FLuaFileTagNode> const & Item:Childs)
		{
			if(InFilterText.Len() != 0)
			{
				if(Item->GetTagName().Contains(InFilterText))
				{
					OutAllChilds.Add(Item);
				}
			}
			else
			{
				OutAllChilds.Add(Item);
			}
			
		}
	}

	TArray<TSharedPtr<FLuaFileTagNode> > const & GetChilds()
	{
		return Childs;
	}
	int32 GetChildNum()
	{
		return Childs.Num();
	}

private:
	FString LuaRequireName;
	TArray<TSharedPtr<FLuaFileTagNode> > Childs;
	bool bCanSelected = false;
};
