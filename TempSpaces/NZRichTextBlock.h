// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/RichTextBlock.h"
#include "NZRichTextBlock.generated.h"

/**
 * 
 */
UCLASS()
class FIRSTCPLUSPLUSDEMO_API UNZRichTextBlock : public URichTextBlock
{
	GENERATED_BODY()
	
public:
	virtual void SetText(const FText& InText);

	/** Text style to apply by default to text in this block */
	UPROPERTY(EditAnywhere, Category = Appearance, meta = (EditCondition = bOverrideDefaultStyle))
	FTextBlockStyle DynamicTextStyle;
};
