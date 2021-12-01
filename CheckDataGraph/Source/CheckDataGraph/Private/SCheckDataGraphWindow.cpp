#include "SCheckDataGraphWindow.h"
#include "CheckData_EdGraph.h"
#include "CheckData_EdGraphSchema.h"

void SCheckDataGraphWindow::Construct(const FArguments& InArgs)
{
	//创建图表对象
	GraphObj = NewObject<UCheckData_EdGraph>();
	GraphObj->Schema = UCheckData_EdGraphSchema::StaticClass();
	GraphObj->AddToRoot();

	GraphObj->RebuildGraph();


	//创建图表编辑器控件
	GraphEditorPtr = SNew(SGraphEditor)
	.GraphToEdit(GraphObj);


	//指定本控件的UI：
	ChildSlot
	[
		GraphEditorPtr.ToSharedRef()
	];
}