// Fill out your copyright notice in the Description page of Project Settings.


#include "NZRichTextBlock.h"
#include "Widgets/Text/SRichTextBlock.h"
#include "Framework/Text/RichTextMarkupProcessing.h"
#include "Internationalization/Regex.h"

void UNZRichTextBlock::SetText(const FText& InText)
{
	Text = InText;

	if (TextStyleSet == nullptr)
	{		
		TextStyleSet = NewObject<UDataTable>(GetTransientPackage(), FName(TEXT("TempDataTable")));
		TextStyleSet->RowStruct = FRichTextStyleRow::StaticStruct();
	}

	TArray<FTextLineParseResults> LineParseResultsArray;
	FString ProcessedString;
	TSharedPtr< IRichTextMarkupParser > Parser = FDefaultRichTextMarkupParser::GetStaticInstance();
	Parser->Process(LineParseResultsArray, InText.ToString(), ProcessedString);

	// Iterate through parsed line results and create processed lines with runs.
	for (int32 LineIndex = 0; LineIndex < LineParseResultsArray.Num(); ++LineIndex)
	{
		const FTextLineParseResults& LineParseResults = LineParseResultsArray[LineIndex];
		for (const FTextRunParseResults& RunParseResult : LineParseResults.Runs)
		{
			if (!RunParseResult.Name.IsEmpty())
			{				
				FRegexPattern ElementRegexPattern = FRegexPattern(TEXT("([a-fA-F]{6})"));
				const FString& Input = RunParseResult.Name;
				FRegexMatcher ElementRegexMatcher(ElementRegexPattern, Input);
				if (ElementRegexMatcher.FindNext())
				{
					// Capture Group 1 is the element name.
					int32 ElementNameBegin = ElementRegexMatcher.GetCaptureGroupBeginning(1);
					int32 ElementNameEnd = ElementRegexMatcher.GetCaptureGroupEnding(1);

					// Name
					FString ElementName = Input.Mid(ElementNameBegin, ElementNameEnd - ElementNameBegin);
					FName StyleName = FName(*ElementName);
					FRichTextStyleRow* result = TextStyleSet->FindRow<FRichTextStyleRow>(StyleName, FString(""), false);
					if (result == nullptr)
					{
						FRichTextStyleRow RowData = FRichTextStyleRow();
						RowData.TextStyle = DefaultTextStyle;
						FColor color = FColor();
						color.FromHex(StyleName.ToString());
						FLinearColor linearColor = FLinearColor(color);
						RowData.TextStyle.SetColorAndOpacity(FSlateColor(linearColor));
						TextStyleSet->AddRow(StyleName, RowData);
					}
				}
			}		
		}
	}

	RebuildStyleInstance();

	if (MyRichTextBlock.IsValid())
	{
		MyRichTextBlock->SetText(InText);
	}
}