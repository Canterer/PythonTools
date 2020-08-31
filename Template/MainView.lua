local XXXMainView = BaseView()

function XXXMainView:Init()
	self:InitData()
	self:InitUI()
	self:RegisterDelegates()
end

function XXXMainView:InitData()
	-- body
end

function XXXMainView:InitUI()
	self.testBtn = self:Wnd("TestBtn")
end

function XXXMainView:RegisterDelegates()
	self.testBtn:Event("cLICK",self.OnTestBtnClicked,self)
end

function XXXMainView:Destory()
end

function XXXMainView:OnShow()
end

function XXXMainView:OnTestBtnClicked()
	-- body
end

function XXXMainView:UpdateTestList()
	-- body
end

return XXXMainView