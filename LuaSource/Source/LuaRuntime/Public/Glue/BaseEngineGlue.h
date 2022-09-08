#pragma once

class FNZLuaConfigCacheIniWrap 
{
public:
	FNZLuaConfigCacheIniWrap(FConfigCacheIni * InInnerConfig);
	~FNZLuaConfigCacheIniWrap();
	TArray<FString> GetArray(FString const & SectionName,FString const & KeyName, FString const & IniName );
	FString GetString( const FString& Section, const FString& Key, const FString& Filename );

private:
	FConfigCacheIni * InnerConfig;
};
