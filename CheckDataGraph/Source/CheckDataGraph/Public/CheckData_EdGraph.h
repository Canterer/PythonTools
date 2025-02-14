// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "EdGraph/EdGraph.h"
#include "CheckData_EdGraph.generated.h"

/**
 * 
 */
UCLASS()
class CHECKDATAGRAPH_API UCheckData_EdGraph : public UEdGraph
{
	GENERATED_BODY()

public:
	//重新构建图表
	void RebuildGraph();
};
