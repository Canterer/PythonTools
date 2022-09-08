#pragma once 
#include "LuaFileSystem/ILuaFile.h"

class FLuaTcpTransport
{
public:
	FLuaTcpTransport();
	~FLuaTcpTransport();
	bool Initialize(const FString & InServerIpAndPort);
	
	bool SendPayloadAndReceiveResponse(TArray<uint8>& In, TArray<uint8>& Out);
	bool ReceiveResponse(TArray<uint8> &Out);
private:
	class FSocket*		FileSocket;
};

class FLuaServerFile : public ILuaFile
{
public:
	FLuaServerFile();
	virtual ~FLuaServerFile();
	// begin ILuaFile
	bool Initialize(NS_SLUA::lua_State * inL) override;
	bool LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath) override;
	// end ILuaFile
	static bool IsEnable();

	bool IsExists(FString const & InFilePath);
	static FString BaseDir();

	static int32 loadfile();
public:
	FString ReadFromFile(FString const & InLuaFile);
	bool CanUseClientFile(FString const & InFilePath);
	bool InitializeInternal(FString const & ServerIpAndPort);
	void readServerIpAndPort(FString & InOutServerIpAndPort);
	FString MakeLuaFileLocal(FString const InLuaRequire);
	FString ConvertToLocalFileName(FString const & InLuaFileName);
	static FString ConvertToCacheFileName(FString const & InLuaFileName);
	bool InLocal(FString const & InLuaFileName);
	bool RequireFromServer(FString const & InLuaFileName);

	static void WriteRemoteServer(FString const & InServerAddress);

	void InitializeLua();
	void GetFileList();
private:
	
	TMap<FString, FDateTime> ClientFileCache;
	class FLuaTcpTransport* Transport;
	FCriticalSection	SynchronizationObject;

	IPlatformFile * InnerPlatformFile;
};
