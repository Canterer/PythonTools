#include "LuaActorBind.h"

#include "LuaBind.h"
#include "GameFramework/Actor.h"


void ULuaActorBindComponent::BeginPlay()
{
	Super::BeginPlay();

	AActor * Owner = GetOwner();
	if(Owner)
	{
		if(!LuaFileTag.IsEmpty())
		{
			LuaCtor(LuaFileTag.ToString(),Owner);
		}
	}
}

void ULuaActorBindComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);

	LuaRelease(GetOwner());
}

