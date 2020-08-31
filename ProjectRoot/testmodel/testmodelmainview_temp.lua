local TestModelMainView = BaseView()

function TestModelMainView:Init()
	self:InitData()
	self:InitUI()
	self:RegisterDelegates()
end

function TestModelMainView:InitData()
	-- body
end

function TestModelMainView:InitUI()
	self.testBtn = self:Wnd("TestBtn")
	self.leftList = self:Wnd("LeftContainer")
	self.rightList = self:Wnd("RightContainer")
end

function TestModelMainView:RegisterDelegates()
	self.testBtn:Event("cLICK",self.OnTestBtnClicked,self)
end

function TestModelMainView:Destory()
end

function TestModelMainView:OnShow()
end

function TestModelMainView:OnTestBtnClicked()
	-- body
end

function TestModelMainView:UpdateTestList()
	-- body
end

function xxxxMainView:UpdateLeftList(dataList)
	self.leftList:Update(dataList)
end

function xxxxMainView:UpdateRightList(dataList)
	self.rightList:Update(dataList)
end

return TestModelMainView