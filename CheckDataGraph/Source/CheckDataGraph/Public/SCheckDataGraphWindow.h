#pragma once

#include "CoreMinimal.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Widgets/SCompoundWidget.h"
#include "GraphEditor.h"

class SCheckDataGraphWindow : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SCheckDataGraphWindow) {}

	SLATE_END_ARGS()

	/** Constructs this widget with InArgs */
	void Construct(const FArguments& InArgs);

	//ͼ��༭���ؼ�
	TSharedPtr<SGraphEditor> GraphEditorPtr;

	//ͼ�����
	class UCheckData_EdGraph* GraphObj;
};