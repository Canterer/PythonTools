#include "SCheckDataGraphWindow.h"
#include "CheckData_EdGraph.h"
#include "CheckData_EdGraphSchema.h"

void SCheckDataGraphWindow::Construct(const FArguments& InArgs)
{
	//����ͼ�����
	GraphObj = NewObject<UCheckData_EdGraph>();
	GraphObj->Schema = UCheckData_EdGraphSchema::StaticClass();
	GraphObj->AddToRoot();

	GraphObj->RebuildGraph();


	//����ͼ��༭���ؼ�
	GraphEditorPtr = SNew(SGraphEditor)
	.GraphToEdit(GraphObj);


	//ָ�����ؼ���UI��
	ChildSlot
	[
		GraphEditorPtr.ToSharedRef()
	];
}