#include "LuaServerFile.h"
//////////////////////////////////////////////////////////////////////////

FLuaTcpTransport::FLuaTcpTransport()
{
	FileSocket = NULL;
}

FLuaTcpTransport::~FLuaTcpTransport()
{
}

bool FLuaTcpTransport::Initialize(const FString& InServerIpAndPort)
{
	ISocketSubsystem* SSS = ISocketSubsystem::Get();

	FString HostIp = InServerIpAndPort;


	// the protocol isn't required for tcp it's assumed by default
	HostIp.RemoveFromStart(TEXT("tcp://"));

	// convert the string to a ip addr structure
	// DEFAULT_TCP_FILE_SERVING_PORT is overridden 
	TSharedRef<FInternetAddr> Addr = SSS->CreateInternetAddr(0, 8006);
	bool bIsValid;

	Addr->SetIp(*HostIp, bIsValid);

	if (bIsValid)
	{
		// create the socket
		FileSocket = SSS->CreateSocket(NAME_Stream, TEXT("FNetworkPlatformFile tcp"));
		UE_LOG(LuaFile, Log, TEXT("Create Soecket %p"), FileSocket);
		// try to connect to the server
		if (FileSocket == nullptr || FileSocket->Connect(*Addr) == false)
		{
			// on failure, shut it all down
			SSS->DestroySocket(FileSocket);
			FileSocket = NULL;
			UE_LOG(LuaFile, Error, TEXT("Failed to connect to file server at %s."), *Addr->ToString(true));
		}
	}
	UE_LOG(LuaFile, Warning, TEXT("Lua Transport Initialize Error FileSocket == NULL bIsValid %d"), bIsValid);
	return FileSocket != NULL;
}

bool FLuaTcpTransport::SendPayloadAndReceiveResponse(TArray<uint8>& In, TArray<uint8>& Out)
{
	if (FileSocket)
	{
		bool SendResult = false;
		SendResult = FNFSMessageHeader::WrapAndSendPayload(In, FSimpleAbstractSocket_FSocket(FileSocket));

		if (!SendResult)
			return false;

		FArrayReader Response;
		bool RetResult = false;

		RetResult = FNFSMessageHeader::ReceivePayload(Response, FSimpleAbstractSocket_FSocket(FileSocket));

		if (RetResult)
		{
			Out.Append(Response.GetData(), Response.Num());
			return true;
		}
	}


	return false;
}


FLuaServerFile::FLuaServerFile()
{
	Transport = nullptr;
}

FString FLuaServerFile::BaseDir()
{
#if WITH_EDITOR
	if (GIsPlayInEditorWorld)
	{
		return FPaths::ProjectSavedDir() / TEXT("LuaSource");
	}
	else
	{
		return FLuaSrcFile::BaseDir();
	}
#endif
	return FLuaSrcFile::BaseDir();
}

bool FLuaServerFile::Initialize(NS_SLUA::lua_State * inL)
{
	InnerPlatformFile = &FPlatformFileManager::Get().GetPlatformFile();
	FString ServerIpAndPort;
	readServerIpAndPort(ServerIpAndPort);
	UE_LOG(LuaFile, Log, TEXT("Get LuaFileServer :%s"), *ServerIpAndPort);

	Transport = new FLuaTcpTransport();
	bool bResult = false;
	if (Transport)
	{
		bResult = Transport->Initialize(*ServerIpAndPort) && InitializeInternal(ServerIpAndPort);
	}

	if (!bResult)
	{
		Transport = nullptr;
		return false;
	}

	GetFileList();

	//InitializeLua(inL);

	return true;
}

void FLuaServerFile::GetFileList()
{
	FNetworkFileArchive Payload(NFS_Messages::GetFileList);
	FArrayReader Out;

	Payload << ClientFileCache;
	if (Transport && Transport->SendPayloadAndReceiveResponse(Payload, Out))
	{
		int32 CMD;

		Out << CMD;

		TMap<FString, FDateTime> ServerFileTime;
		Out << ServerFileTime;

		for (auto& item : ServerFileTime)
		{
			if (ClientFileCache.Contains(item.Key))
			{
				ClientFileCache.Remove(item.Key);
			}
		}

	}
}

void FLuaServerFile::InitializeLua()
{

}

bool FLuaServerFile::LoadFileContent(const char * fn,TArray<uint8> & OutContent,FString & InFilePath)
{
// 	FString LuaString = FString::Printf(TEXT("require \"%s\""), *InFilePath);
// 	if (luaL_dostring(inL, TCHAR_TO_UTF8(*LuaString)))
// 	{
// 		FString errorMsg = UTF8_TO_TCHAR(lua_tostring(inL, -1));
// 		UE_LOG(LuaFile, Log, TEXT("Do File Error %s"), *errorMsg);
// 	}

	return false;
}

void FLuaServerFile::readServerIpAndPort(FString& InOutServerIpAndPort)
{
	FString CommandlineFilePath = FLuaSrcFile::BaseDir() / TEXT("luacommandline.txt");
	IPlatformFile* PlatformFile = &FPlatformFileManager::Get().GetPlatformFile();
	if (PlatformFile && PlatformFile->FileExists(*CommandlineFilePath))
	{
		IFileHandle* FileHandle = PlatformFile->OpenRead(*CommandlineFilePath);
		if (FileHandle)
		{
			uint8  CommandlineTXT[4096] = { 0 };
			if (FileHandle->Read(CommandlineTXT, FileHandle->Size()))
			{
				FString Commandline = UTF8_TO_TCHAR(CommandlineTXT);

				FParse::Value(*Commandline, TEXT("FileHostIP="), InOutServerIpAndPort, true);
			}
			delete FileHandle;
		}
	}
}

bool FLuaServerFile::InitializeInternal(FString const& ServerIpAndPort)
{
	class LuaSourceFileStatDirVisitor : public IPlatformFile::FDirectoryStatVisitor
	{
	public:
		LuaSourceFileStatDirVisitor(TMap<FString, FDateTime>& OutCache) :InCache(OutCache) {}
	public:
		virtual bool Visit(const TCHAR* FilenameOrDirectory, const FFileStatData& StatData) override
		{
			if (!StatData.bIsDirectory)
			{
				FString ClientLuaPathName = FPaths::ConvertRelativePathToFull(FilenameOrDirectory);
				if (ClientLuaPathName.EndsWith(TEXT(".lua")))
				{
					ClientLuaPathName = FLuaServerFile::ConvertToCacheFileName(ClientLuaPathName);

					InCache.Add(ClientLuaPathName, StatData.CreationTime);
				}

			}

			return true;
		}
	private:
		TMap<FString, FDateTime>& InCache;
	} viritor(ClientFileCache);


	FNetworkFileArchive Payload(NFS_Messages::Heartbeat);
	FArrayReader Out;

	if (Transport && Transport->SendPayloadAndReceiveResponse(Payload, Out))
	{

		FPlatformFileManager::Get().GetPlatformFile().IterateDirectoryStatRecursively(*FLuaServerFile::BaseDir(), viritor);

		return true;
	}

	return false;
}



FLuaServerFile::~FLuaServerFile()
{
	InnerPlatformFile = nullptr;
}


bool FLuaServerFile::IsExists(FString const& InFilePath)
{
	return false;
}

bool FLuaServerFile::CanUseClientFile(FString const& InFilePath)
{
	return false;
}


bool FLuaServerFile::IsEnable()
{
#if ALLOW_DEBUG_FILES
#if WITH_EDITOR
	if (!GIsPlayInEditorWorld)
	{
		return false;
	}
#endif
	FString CommandlineFilePath = FLuaSrcFile::BaseDir() / TEXT("luacommandline.txt");

	IPlatformFile* PlatformFile = &FPlatformFileManager::Get().GetPlatformFile();

	if (PlatformFile && PlatformFile->FileExists(*CommandlineFilePath))
	{
		return true;
	}
#endif 

	return false;
}

int32 FLuaServerFile::loadfile()
{
// 	FLuaServerFile* LuaFileInterface = (FLuaServerFile*)lua_touserdata(inL, lua_upvalueindex(1));
// 
// 	FString LuaObjName = lua_tostring(inL, 1);
// 	FString LuaFileName = LuaFileInterface->MakeLuaFileLocal(LuaObjName);
// 
// #if PLATFORM_IOS
// 	FString iOSLuaFile = FString([NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES) objectAtIndex:0]) / LuaFileName;
// 
// 	if (luaL_dofile(inL, TCHAR_TO_UTF8(*iOSLuaFile)) == LUA_OK)
// 	{
// 		return 1;
// 	}
// 	else
// 	{
// 		FString errorMsg = UTF8_TO_TCHAR(lua_tostring(inL, -1));
// 		UE_LOG(LuaFile, Log, TEXT("FLuaServerFile(IOS) loadFile Error %s"), *errorMsg);
// 		lua_pop(inL, 1);
// 	}
// #endif
// 
// 
// 	FString Code = LuaFileInterface->ReadFromFile(LuaFileName);
// 	if (Code.Len() > 0)
// 	{
// 		if (luaL_loadstring(inL, TCHAR_TO_UTF8(*Code)) == LUA_OK)
// 		{
// 			return 1;
// 		}
// 		else
// 		{
// 			FString errorMsg = UTF8_TO_TCHAR(lua_tostring(inL, -1));
// 			UE_LOG(LuaFile, Log, TEXT("FLuaServerFile loadFile Error %s"), *errorMsg);
// 		}
// 	}

	return 0;
}

FString FLuaServerFile::MakeLuaFileLocal(FString const InLuaRequire)
{
	if (!InLocal(InLuaRequire))
	{
		RequireFromServer(InLuaRequire);
	}

	return ConvertToLocalFileName(InLuaRequire);
}

bool FLuaServerFile::InLocal(FString const& InLuaFileName)
{
	FString LuaFileName = ConvertToLocalFileName(InLuaFileName);

	if (FPaths::FileExists(LuaFileName))
	{
		if (ClientFileCache.Contains(InLuaFileName))
		{
			FDateTime const& LuaFileCreateTime = *ClientFileCache.Find(InLuaFileName);

			FDateTime LuaClientTime = InnerPlatformFile->GetTimeStamp(*LuaFileName);
			if (LuaClientTime < LuaFileCreateTime)
			{
				return false;
			}
			else
			{
				return true;
			}
		}
		else
		{
			return false;
		}
	}

	return false;
}

FString FLuaServerFile::ConvertToLocalFileName(FString const& InLuaFileName)
{
	FString LuaFileName = InLuaFileName;
	LuaFileName.RemoveFromEnd(TEXT(".lua"));
	LuaFileName = InLuaFileName.Replace(TEXT("."), TEXT("/"));
	LuaFileName += TEXT(".lua");

	LuaFileName = FLuaServerFile::BaseDir() / LuaFileName;

	LuaFileName = FPaths::ConvertRelativePathToFull(LuaFileName);
	UE_LOG(LuaFile, Log, TEXT("FLuaServerFile ConvertToLocalFileName %s->%s"), *InLuaFileName, *LuaFileName);

	return LuaFileName;
}

FString FLuaServerFile::ConvertToCacheFileName(FString const& InLuaFileName)
{
	FString LuaFileName = FPaths::ConvertRelativePathToFull(InLuaFileName);
	FString BaseFullDir = FLuaServerFile::BaseDir();
	BaseFullDir = FPaths::ConvertRelativePathToFull(BaseFullDir);
	LuaFileName.RemoveFromEnd(TEXT(".lua"));


	LuaFileName.RemoveFromStart(BaseFullDir);

	FPaths::NormalizeFilename(LuaFileName);
	LuaFileName.ReplaceInline(TEXT("/"), TEXT("."));

	LuaFileName.RemoveFromStart(TEXT("."));
	// debug. ?
	LuaFileName.RemoveFromStart(TEXT("debug."));
	return LuaFileName;
}


bool FLuaServerFile::RequireFromServer(FString const& InLuaFileName)
{
	FNetworkFileArchive Payload(NFS_Messages::Read);
	FString LuaFileName = InLuaFileName;
	Payload << LuaFileName;

	FArrayReader Out;
	if (Transport && Transport->SendPayloadAndReceiveResponse(Payload, Out))
	{
		IPlatformFile& IFile = FPlatformFileManager::Get().GetPlatformFile();
		int32 CMD;
		Out << CMD;

		FString ServerFileName;
		Out << ServerFileName;

		FDateTime ServerDateTime;
		Out << ServerDateTime;

		TArray<uint8> LuaCode;
		Out << LuaCode;

		ClientFileCache.Emplace(InLuaFileName, ServerDateTime);


		FString ClientLuaFileName = ConvertToLocalFileName(InLuaFileName);

		FString ClientLuaFilePath = FPaths::GetPath(ClientLuaFileName);

		if (!IFile.DirectoryExists(*ClientLuaFilePath))
		{
			IFile.CreateDirectoryTree(*ClientLuaFilePath);
		}
		if (FPaths::FileExists(ClientLuaFileName))
		{
			IFile.DeleteFile(*ClientLuaFileName);
		}


		IFileHandle* FileHandle = IFile.OpenWrite(*ClientLuaFileName);
		ensureAlwaysMsgf(FileHandle, TEXT("Check..."));
		if (FileHandle)
		{

			FileHandle->Write(LuaCode.GetData(), LuaCode.Num());

			UE_LOG(LuaFile, Log, TEXT("Recv %s Size %d"), *ServerFileName, LuaCode.Num());


			FileHandle->Flush();

			delete FileHandle;
			return true;
		}

		IFile.SetTimeStamp(*ClientLuaFileName, ServerDateTime);

	}

	return false;


}

FString FLuaServerFile::ReadFromFile(FString const& InFilePathName)
{
	IPlatformFile& IFile = FPlatformFileManager::Get().GetPlatformFile();
	IFileHandle* FileHandle = IFile.OpenRead(*InFilePathName);
	if (FileHandle && FileHandle->Size() > 0)
	{
		TArray<uint8> OutData;
		OutData.SetNum(FileHandle->Size() + 1);
		FileHandle->Read(OutData.GetData(), FileHandle->Size());
		OutData[OutData.Num() - 1] = 0;
		delete FileHandle;
		FileHandle = NULL;
		return FString(UTF8_TO_TCHAR(OutData.GetData()));
	}

	return TEXT("");
}

void FLuaServerFile::WriteRemoteServer(FString const& InServerAddress)
{
	FString BaseDir = FLuaSrcFile::BaseDir();


	IPlatformFile& IFile = FPlatformFileManager::Get().GetPlatformFile();

	if (!IFile.DirectoryExists(*BaseDir))
	{

		bool Result = IFile.CreateDirectoryTree(*BaseDir);

		UE_LOG(LuaFile, Log, TEXT("LuaServerFile Check Directory Is not Exists Create %d"), Result);
	}
	FString CommandFilePath = BaseDir / TEXT("luacommandline.txt");

	bool bAppend = IFile.FileExists(*CommandFilePath);

	IFileHandle* WriteFileHandle = IFile.OpenWrite(*CommandFilePath, bAppend);
	if (WriteFileHandle)
	{
		FString commandline = TEXT(" -FileHostIP=") + InServerAddress;
		TArray<uint8> content;
		content.SetNum(commandline.Len());
		memcpy(content.GetData(), TCHAR_TO_ANSI(*commandline), commandline.Len());
		WriteFileHandle->Write(content.GetData(), content.Num());
		WriteFileHandle->Flush();
		delete WriteFileHandle;
		WriteFileHandle = nullptr;

		UE_LOG(LuaFile, Log, TEXT("LuaSrcFile WriteRemoteServer Success!!!"));
	}
	else
	{
		UE_LOG(LuaFile, Warning, TEXT("LuaSrcFile WriteRemoteServer OpenWrite return NULL!!!"));
	}
}
