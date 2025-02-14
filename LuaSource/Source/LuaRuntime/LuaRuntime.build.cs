// Fill out your copyright notice in the Description page of Project Settings.

using UnrealBuildTool;

public class LuaRuntime : ModuleRules
{
    public LuaRuntime(ReadOnlyTargetRules Target)
        : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		bEnableExceptions = true;
		bEnforceIWYU = false;
		bEnableUndefinedIdentifierWarnings = false;

		PublicIncludePaths.AddRange(new string[]{
            
        });

        PrivateIncludePaths.AddRange(new string[]{

            
        });

        PublicDependencyModuleNames.AddRange(new string[]{
            "Core",
            "CoreUObject",
            "Engine",
			"Sockets",
			"UMG",
			"SlateCore",
			"Slate",
			"slua_unreal",
			"GlobalMessageRuntime",
			"GameCore",
		});  
    }
}
