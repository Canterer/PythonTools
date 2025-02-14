import os
import sys
import psutil
from pywinauto import Application

bLoopFlag = True

def LogObject(Obj):
    for attr in dir(Obj):
        if not attr.startswith('__'):
            print(f"{attr}:{getattr(Obj, attr)}")

def get_pid_list_by_name(process_name):
    return [p.pid for p in psutil.process_iter(['name']) if p.info['name'] == process_name]

def loopFunc(app):
    #等待无通话
    VoipPanel = app.window(title="微信", class_name="VoipWnd")
    VoipPanel.wait_not(wait_for_not="exists", timeout=10, retry_interval=1)
    #等待通话请求
    TipPanel = app.window(title="微信", class_name="VoipTrayWnd")
    TipPanel.wait(wait_for="exists", timeout=10, retry_interval=1)
    video_call_windowSpec = TipPanel.child_window(title_re=".*邀请你视频通话", control_type="Button")
    voice_call_windowSpec = TipPanel.child_window(title_re=".*邀请你语音通话", control_type="Button")
    if video_call_windowSpec.exists() or voice_call_windowSpec.exists():
        print("video_call:{0} voice_call:{0}".format(video_call_windowSpec.exists(),voice_call_windowSpec.exists()))
        accept_btn_windowSpec = TipPanel.child_window(title="接受", control_type="Button")
        if accept_btn_windowSpec.exists():
            print("Find Accept Call Btn")
            accept_btn_windowSpec.click_input()
            #bLoopFlag = False
            
    
 
def main(*args):
    print("args:",*args)
    print("Test pywinauto")
    
    app = Application(backend='uia')
    
    pid_list = get_pid_list_by_name("WeChat.exe")
    if len(pid_list) > 0:
        app.connect(process=pid_list[0])
    else:
        app.start(r"E:\Softs\WeChat\WeChat.exe")
    #app.connect(process=22500)
    print("WeChat.exe pid=",app.process)
    #dlg = app.window(title="Notepad++")
    #dlg = app.window(title="微信")
    #print("is64bit:", app.is64bit())
    #print("cpu_usage:", app.cpu_usage())

    
    
    MainWnd = app.window(title="微信",class_name="WeChatMainWndForPC")
    if MainWnd.exists():
        print("MainWnd Panel")

    bLoopFlag = True
    while bLoopFlag:
        try:
            loopFunc(app)
        except Exception as e:
            print("Loop exception:", e)

    bTest = True
    if not bTest:
        return
    
    wrappers = app.windows()
    for wrapper in wrappers:
        print("\ngetWindow type:{0} title:'{1}' class_name:{2}".format(wrapper.friendly_class_name(), wrapper.window_text(), wrapper.element_info.class_name))
        list_data = wrapper.children()
        for index, item in enumerate(list_data):
            element_info = item.element_info
            print("\n\tindex={2} child title:{0} class_name:{1}".format(item.window_text(), item.friendly_class_name(), index))
            print("\telement_info name:'{0}' class_name:'{1}'".format(element_info.name, element_info.class_name))
            print("\trectangle:", element_info.rectangle)
            print("\tchildren:", element_info.children())
            print("\titer_children:", element_info.iter_children())

        if wrapper.friendly_class_name() != "Dialog":
            windowSpec = app.window(title=wrapper.window_text(),class_name=wrapper.element_info.class_name)
            windowSpec.print_control_identifiers()
            video_call_windowSpec = windowSpec.child_window(title_re=".*邀请你视频通话", control_type="Button")
            voice_call_windowSpec = windowSpec.child_window(title_re=".*邀请你语音通话", control_type="Button")
            if video_call_windowSpec.exists() or voice_call_windowSpec.exists():
                print("video_call:{0} voice_call:{0}".format(video_call_windowSpec.exists(),voice_call_windowSpec.exists()))
                accept_btn_windowSpec = windowSpec.child_window(title="接受", control_type="Button")
                if accept_btn_windowSpec.exists():
                    print("Find Accept Call Btn")
                    accept_btn_windowSpec.click_input()
        elif bTest:
            windowSpec = app.window(title=wrapper.window_text(),class_name=wrapper.element_info.class_name)
            if wrapper.window_text() == "杨成可" and wrapper.element_info.class_name == "ChatWnd":
                #windowSpec.print_control_identifiers()
                #pop_panel_windowSpec = windowSpec.child_window(title="发送(S)",control_type="Button")
                #LogObject(pop_panel_windowSpec)
                t = windowSpec.child_window(title_re=".*",control_type="Button")
                #child_wrapper = t.wrapper_object();
                #child_list_data = child_wrapper.children()
                #for index, item in enumerate(child_list_data):
                    #print("\n\tindex={2} child title:{0} class_name:{1}".format(item.window_text(), item.friendly_class_name(), index))
                    #print("\n\telement_info title:{0} class_name:{1}".format(item.window_text(), item.element_info.class_name))
                
                #print(type(t))
                #t.click_input()
                
                #pop_panel_windowSpec.print_control_identifiers()
                #if pop_panel_windowSpec.exists():
                    #print("Find!!!!!")
                #windowSpec.child_window(title="杨成可",control_type="Dialog")
            
                #windowSpec.print_control_identifiers()
            

        

    #print("get_show_state:", dlg.get_show_state())
    #dlg.print_control_identifiers()

    #btn_yuyin = dlg.child_window(title="语音聊天", control_type="Button")
    #btn_video = dlg.child_window(title="视频聊天", control_type="Button")
    
    
    #list_data = dlg.child_window(control_type="Pane")

    

if __name__ == "__main__":
    main(*sys.argv[1:])
