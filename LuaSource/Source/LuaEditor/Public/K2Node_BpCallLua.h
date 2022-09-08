// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "K2Node_EditablePinBase.h"
#include "K2Node_AddPinInterface.h"
#include "K2Node_BpCallLua.generated.h"

/**
 * 
 */
UCLASS()
class LUAEDITOR_API UK2Node_BpCallLua : public UK2Node,public IK2Node_AddPinInterface
{
	GENERATED_UCLASS_BODY()
public:
	//UEdGraphNode implementation
	virtual void AllocateDefaultPins() override;
	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;

	//K2Node implementation
	virtual void GetNodeContextMenuActions(class UToolMenu* Menu,
										   class UGraphNodeContextMenuContext* Context) const override;

	void RemoveInputPin(UEdGraphPin* Pin);
	bool CanRemovePin(const UEdGraphPin * Pin) const;
	virtual FText GetMenuCategory() const override;
	virtual void PostReconstructNode() override;
	virtual void ExpandNode(class FKismetCompilerContext& CompilerContext, UEdGraph* SourceGraph) override;
	virtual void GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const override;
	virtual void NotifyPinConnectionListChanged(UEdGraphPin* Pin) override;
	virtual void AddInputPin();
	void AddOutputPin();
private:
	
	void AddInputPinsInner(int32 PinIndex);
	UEdGraphPin * GetInputPin(int32 PinIndex);
	UEdGraphPin * GetOutputPin(int32 PinIndex);
private:
	UPROPERTY()
		int32 InputPinNums;
	UPROPERTY()
		int32 OutputPinNums;
	UPROPERTY()
	int32 VaildInputPinNum;
};
