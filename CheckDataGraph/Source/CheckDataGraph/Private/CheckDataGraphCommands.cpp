// Copyright Epic Games, Inc. All Rights Reserved.

#include "CheckDataGraphCommands.h"

#define LOCTEXT_NAMESPACE "FCheckDataGraphModule"

void FCheckDataGraphCommands::RegisterCommands()
{
	UI_COMMAND(OpenPluginWindow, "CheckDataGraph", "Bring up CheckDataGraph window", EUserInterfaceActionType::Button, FInputGesture());
}

#undef LOCTEXT_NAMESPACE
