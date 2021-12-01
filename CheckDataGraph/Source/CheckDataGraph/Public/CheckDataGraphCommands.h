// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/Commands/Commands.h"
#include "CheckDataGraphStyle.h"

class FCheckDataGraphCommands : public TCommands<FCheckDataGraphCommands>
{
public:

	FCheckDataGraphCommands()
		: TCommands<FCheckDataGraphCommands>(TEXT("CheckDataGraph"), NSLOCTEXT("Contexts", "CheckDataGraph", "CheckDataGraph Plugin"), NAME_None, FCheckDataGraphStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > OpenPluginWindow;
};