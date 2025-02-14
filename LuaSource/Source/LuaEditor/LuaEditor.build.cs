// Fill out your copyright notice in the Description page of Project Settings.

using UnrealBuildTool;

public class LuaEditor : ModuleRules
{
    public LuaEditor(ReadOnlyTargetRules Target)
        : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(new string[]{
            
        });

        PrivateIncludePaths.AddRange(new string[]{

            
        });

        PublicDependencyModuleNames.AddRange(new string[]{
            "Core",
            "CoreUObject",
            "Engine",
            "UnrealEd",
			"PropertyEditor",
			"BlueprintGraph",
			"KismetCompiler",
			"ToolMenus",
			"Slate",
			"SlateCore",
			"InputCore",
			"EditorStyle",
			"Projects",
			"UMG",
			"slua_unreal",
			"LuaRuntime"
			
        });
		PrivateDependencyModuleNames.AddRange(new string[] {
			"Settings"
		});

	}
}
