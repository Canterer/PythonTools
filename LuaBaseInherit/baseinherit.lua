local LogDeep = function(n)
    local logStr = "ZX"
    for i = 1, n do
        local info = debug.getinfo(i,"Sln")
        if not info then
            return logStr
        end
        -- print(string.format("%s:%s >>> %s(...)\n",string.sub(info.short_src,10),info.currentline,info.name))
        logStr = logStr..string.format("%s:%s >>> %s(...)\n",string.sub(info.short_src,10),info.currentline,info.name)
    end
    return logStr
end
GRecordIns = setmetatable({},{__mode="k"})
GRecordInsInfo = {}

GBaseInheritClass = GBaseInheritClass or {}
GBaseInheritClass.__index = GBaseInheritClass

local CtorStr = "Ctor"
local DestructStr = "Destruct"
local DestructFlag = "__destruct__"
-- function GBaseInheritClass:Ctor()
-- end

function GBaseInheritClass:Destruct()
    ZS("GBaseInheritClass Destruct",tostring(self))
    rawset(self,DestructFlag,true)
end

function ConstructRecursively(theclass, ins)
	if theclass == nil then return end
    local super = rawget(theclass,"_meta_")
	if super then
		ConstructRecursively(super, ins)
	end
    local Ctor = rawget(theclass, CtorStr)
	if Ctor then 
        if not GRecordIns[ins] then
            GRecordIns[ins] = true
            GRecordInsInfo[ins] = LogDeep(10)
            -- ZS("ConstructRecursively",tostring(ins))
            -- ZS(LogDeep(10))
        end
        Ctor(ins)
    end
end

function DestructRecursively(theclass,ins)
    if theclass == nil then return end
    local Destruct = rawget(theclass, DestructStr)
	if Destruct then
        if GRecordIns[ins] then
            GRecordIns[ins] = nil
        end 
        Destruct(ins)
    end

	local super = rawget(theclass,"_meta_")
	if super then
		DestructRecursively(super, ins)
	end
end

function CheckInheritClass(inheritClass)
    return inheritClass.__index == inheritClass
end

function Inherit(BaseLuaClass)
    -- CheckInheritClass(BaseLuaClass)
    local subLuaClass = {}
    setmetatable(subLuaClass,BaseLuaClass)
    rawset(subLuaClass,"_meta_",BaseLuaClass)
    subLuaClass.__index = subLuaClass
    return subLuaClass
end

function NewInstanceTable(BaseLuaClass)
    local gcFunc = function(t)
        if not rawget(t,DestructFlag) then
            DestructRecursively(BaseLuaClass, t)
        end
    end
    local ins = setmetatable({}, {__index=BaseLuaClass,__gc=gcFunc})
    rawset(ins,"_meta_",BaseLuaClass)--为了可以直接与cppins绑定 触发构造析构
    ConstructRecursively(BaseLuaClass,ins)
    return ins
end


local __UObject_MetaTable = __UObject_MetaTable
local __UObject_MetaTable_index = __UObject_MetaTable.__index
local __UObject_MetaTable_newindex = __UObject_MetaTable.__newindex
-- slua_unreal里的lua流程 创建dofile 初始化Initialize 销毁OnDestroy
--由ULuaUserWidget触发的dofile 会构建lua类实例对象并赋予成员函数
--Initialize方法会给自身进行成员变量初始化
local CppInsStr = "__cppinst"
local slua_unreal_begin_func_name = "Initialize"
local slua_unreal_end_func_name = "OnDestroy"


-- ULuaUserWidget会将自身指针转换为userdata包裹在LuaPath对应的lua类中
-- userdata 被包裹在Lua类里 意味着其lua实例需要特殊的index元方法
-- lua类不包含userdata才具备继承关系,理论上继承关系的lua类可以各自包裹userdata
-- 但实际上每个lua类实例 仅会包裹一个userdata,其父类lua不会再包裹userdata

-- lua类实例需要模拟继承关系的构建析构流程
-- 在Initialize里给lua类 包裹userdata 设置元方法
-- Wnd里对获取的userdata 进行类的实例化
function NewLuaCppMate(luaClass)--cppIns为userdata 存放luaClass实例的CppInsStr域 
    local ins = {}
    ins.__index = function(t, k)
        local func = luaClass[k]--luaClass仅是一系列接口
        if func then return func end
        local success,v = pcall(__UObject_MetaTable_index,t,k)
        if success then
            return v
        end
    end
    ins.__newindex = function(t, k, v)
        local success,v = pcall(__UObject_MetaTable_index,t,k)
        if success then
            pcall(__UObject_MetaTable_newindex,t,k,v)
        else
            rawset(t,k,v)
        end
    end
    return ins
end

-- lua结合cpp 两种: ULuaUserWidget指定的lua文件、UserData外接lua的函数接口
function luaCppTable(cppIns, luaTable)
    local meta = NewLuaCppMate(luaTable)
    meta.__gc = function(ins)
        if not rawget(ins, DestructFlag) then
            DestructRecursively(luaTable,ins)
            rawset(t,CppInsStr,nil)
        end
    end

    local ins = setmetatable({},meta)
    -- Initialize OnDestroy 纯userdata并不需要 仅ULuaUserWidget需要
    -- 统一接口 即实际使用中userdata与ULuaUserWidget使用一个元表
    rawset(ins,slua_unreal_begin_func_name,function(ins)
        rawset(ins,CppInsStr,cppIns)
        ConstructRecursively(luaTable,ins)
    end)
    rawset(ins,slua_unreal_end_func_name,function(ins)
        DestructRecursively(luaTable,ins)
        rawset(ins,CppInsStr,nil)
        -- rawset(ins,DestructFlag,true)
    end)
    ins[slua_unreal_begin_func_name](ins)--触发luaTable构造过程 对ins进行成员变量初始化
    return ins
end

-- 以上为cppIns与lua类结合 可调用两者的接口
-- 以下为cppIns纯绑定lua类 lua接口在两端调用
function OverrideLuaInsMeta(luaIns, BaseClass)
    local Initialize = function(t)
        local meta = getmetatable(t)
        if meta ~= BaseClass then--蓝图修改过对象的元表
            -- setmetatable(meta, BaseClass)
            local indexFunc = function(t,k)
                local func = BaseClass[k]
                if func then return func end
                local success,v = pcall(meta.__index,t,k)
                if success then
                    return v
                end
            end
            local newIndexFunc = function(t,k,v)
                local success,vv = pcall(meta.__index,t,k)
                if success and vv ~= nil then
                    pcall(meta.__newindex,t,k,v)
                else
                    rawset(t,k,v)
                end
            end
            local gcFunc = function(t)
                ZS(rawget(t,DestructFlag))
                ZS("OverrideLuaInsMeta GC",tostring(t))
                if not rawget(t, DestructFlag) then
                    DestructRecursively(luaIns,t)
                end
            end
            setmetatable(t,{__index = indexFunc,__newindex = newIndexFunc,__gc = gcFunc})
        end
        ConstructRecursively(luaIns, t)
    end
    rawset(luaIns,slua_unreal_begin_func_name,Initialize)--重构元表
    rawset(luaIns,slua_unreal_end_func_name,function(t)
        DestructRecursively(luaIns,t)
        ZS("OverrideLuaInsMeta DestructRecursively",tostring(luaIns))
        -- ZS(LogDeep(10))
    end)
end
function NewUILuaClassOverride(BaseClass)
    local ins = Inherit(BaseClass)
    OverrideLuaInsMeta(ins, BaseClass)
    return ins
end

-- LuaCtor(TCHAR_TO_ANSI(*LuaPath),this)
-- 触发FLuaBindBridge:init(const T* ptrT, FString const& luaPath)
-- 其中存放SLUA_CPPINST、使用FLuaBindBridge::__index取值
-- 触发LuaPath对应的对象Initialize方法