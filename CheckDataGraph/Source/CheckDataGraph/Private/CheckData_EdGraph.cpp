// Fill out your copyright notice in the Description page of Project Settings.


#include "CheckData_EdGraph.h"
#include "CheckData_EdGraphNode.h"

void UCheckData_EdGraph::RebuildGraph()
{
	//����һ���ڵ�
	CreateNode(UCheckData_EdGraphNode::StaticClass());
}