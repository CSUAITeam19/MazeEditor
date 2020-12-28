
import multiprocessing
import threading
import numpy as np
from tkinter import *
from threading import Thread
import datetime
import time
import psutil
from psutil import Process
import zmq,sys,os
import json
from mcpi import minecraft
from mcpi import block
from mcpi import vec3
import subprocess

root = Tk()    #消除多窗口的影响
root.withdraw()
MCBLOCK_start = PhotoImage(file='./Resource/img/diamond_ore.png')
MCBLOCK_end = PhotoImage(file='./Resource/img/diamond_block.png')
MCBLOCK_road = PhotoImage(file='./Resource/img/grass_block_top.png')
MCBLOCK_wall = PhotoImage(file='./Resource/img/stone.png')
BackGround = PhotoImage(file='./Resource/img/background.png')

class Block:
    def __init__(self,width_,height_,i_,j_):
        global counter, Maze_Area
        self.i=i_
        self.j=j_
        self.width = width_
        self.height = height_
        counter[self.i][self.j]=1
        self.image = Maze_Area.create_image(self.width*self.i+15,self.height*self.j+15,image=MCBLOCK[counter[self.i][self.j]%2])
    
        

    def co(self,button):
        global counter
        counter[self.i][self.j]+=1
        self.image = Maze_Area.create_image(self.width*self.i+15,self.height*self.j+15,image=MCBLOCK[counter[self.i][self.j]%2])
        
class Block_borden:
    def __init__(self,width_,height_,i_,j_):
        global counter
        self.i=i_
        self.j=j_
        self.width = width_
        self.height = height_
        self.image = Maze_Area.create_image(self.width*self.i+15,self.height*self.j+15,image=MCBLOCK_wall)

class Block_start(Block_borden):
    def __init__(self,width_,height_,i_,j_):
        global counter
        super().__init__(width_,height_,i_,j_)
        self.image = Maze_Area.create_image(self.width*self.i+15,self.height*self.j+15,image=MCBLOCK_start)
        counter[self.i][self.j]=4

class Block_end(Block_borden):
    def __init__(self,width_,height_,i_,j_):
        global counter
        super().__init__(width_,height_,i_,j_)
        self.image = Maze_Area.create_image(self.width*self.i+15,self.height*self.j+15,image=MCBLOCK_end)
        counter[self.i][self.j]=8

def init_B(counter):  #初始化B
    global Maze_Area, B, size_, size_w, size_h, Control_list, Maze_Frame_sb_x, Maze_Frame_sb_y, width_g, height_g

    Maze_Frame = Frame(top, width=dx, height=dx)
    Maze_Frame.place(x=0, y=0)

    Maze_Area = Canvas(Maze_Frame, background='white')

    Maze_Frame_sb_y = Scrollbar(Maze_Frame, orient=VERTICAL)
    Maze_Frame_sb_y.pack(side=RIGHT, fill=Y)
    Maze_Area.config(yscrollcommand=Maze_Frame_sb_y.set)
    Maze_Frame_sb_y.config(command=Maze_Area.yview)
    Maze_Area.pack()
    Maze_Area.config(width=dx, height=dx, scrollregion=(0,0,size_*counter.shape[0],size_*counter.shape[1]))
    Maze_Frame_sb_x = Scrollbar(Maze_Frame, orient=HORIZONTAL)
    Maze_Frame_sb_x.pack(side=BOTTOM, fill=X)
    Maze_Area.config(xscrollcommand=Maze_Frame_sb_x.set)
    Maze_Frame_sb_x.config(command=Maze_Area.xview)


    
    Control_list.append(Maze_Frame_sb_x)
    Control_list.append(Maze_Frame_sb_y)
    Control_list.append(Maze_Area)
    Control_list.append(Maze_Frame)

    start_time=datetime.datetime.now()
    #top.update_idletasks()
    counter_=counter.copy()
    B=np.empty([counter_.shape[0],counter_.shape[1]],dtype=Block)
    flag_start=False
    flag_end=False
    i = 0

    while i < counter.shape[0]:
        j = 0

        while j < counter.shape[1]:

            if counter[i][j]==4:
                B[i][j]=Block_start(width_=size_,height_=size_,i_=i,j_=j)  #起点block
                flag_start = True

            elif counter[i][j]==8:
                B[i][j]=Block_end(width_=size_,height_=size_,i_=i,j_=j)  #终点block
                flag_end = True

            elif i==0 or i==counter_.shape[0]-1 or j== 0 or j==counter_.shape[1]-1:   
                B[i][j]=Block_borden(width_=size_,height_=size_,i_=i,j_=j)    #边界block

            else:
                B[i][j]=Block(width_=size_,height_=size_,i_=i,j_=j)

            j += 1
        i += 1

    if flag_start == False:
        B[1][1]=Block_start(width_=size_,height_=size_,i_=1,j_=1)
    
    if flag_end == False:
         B[counter_.shape[0]-2][counter_.shape[1]-2]=Block_end(width_=size_, height_=size_, i_=counter_.shape[0]-2, j_=counter_.shape[1]-2)

    counter=counter_.copy()
    end_time=datetime.datetime.now()
    Add_logs('[Server]:initB所花费时间:'+str(end_time-start_time))
    width_g = counter.shape[0]
    height_g = counter.shape[1]
    return B

def save_data():                #1,2,4,8为墙壁、路
    global B,counter
    if Maze_checker()==False:
        return

    counter_=counter.copy()  #复制一下
    for i in range(counter_.shape[0]):
        for j in range(counter_.shape[1]):
           
            if counter_[i][j]%2 == 0 and type(B[i][j])==Block or type(B[i][j])==Block_borden:   #数据规范化处理
                counter_[i][j]=1

            elif counter_[i][j]%2 == 1 and type(B[i][j])==Block:
                counter_[i][j]=2

    counter_=counter_.copy().T

      
    np.savetxt(r'./RecFiles/Maze_.txt',counter_,fmt='%d')
    with open(r'./RecFiles/Maze_for_c.txt','w') as file:
        file.write(str(width_g)+' '+str(height_g))
        for i in range(counter_.shape[0]):
            file.write('\n')
            for j in range(counter_.shape[1]):
                file.write(str(counter_[i][j])+' ')

    Add_logs('[Server]:Save data successfully')

def load_data(path=r'./RecFiles/Maze_.txt'):                #1,2,4,8为墙壁、路
    global counter,Block_list,B,width_g,height_g,Control_list,size_,size_w,size_h,Maze_Area
    destroy_all(Control_list)   #清空之前的屏幕
    try:
        counter_=np.loadtxt(path)    #导入数据
    except:
        Add_logs('[Server]:Can not find the Maze.txt!')
        main_loop()


    counter_=np.array(counter_,dtype=int).T
    counter=counter_.copy()

    Maze_Frame = Frame(top, width=dx, height=dx)
    Maze_Frame.place(x=0, y=0)

    Maze_Area = Canvas(Maze_Frame, background='white')
    Maze_Area.config(width=dx, height=dx, scrollregion=(0,0,size_*counter.shape[0],size_*counter.shape[1]))
    Maze_Frame_sb_x = Scrollbar(Maze_Frame, orient=HORIZONTAL)
    Maze_Frame_sb_x.pack(side=BOTTOM, fill=X)
    Maze_Area.config(xscrollcommand=Maze_Frame_sb_x.set)
    Maze_Frame_sb_x.config(command=Maze_Area.xview)

    Maze_Frame_sb_y = Scrollbar(Maze_Frame, orient=VERTICAL)
    Maze_Frame_sb_y.pack(side=RIGHT, fill=Y)
    Maze_Area.config(yscrollcommand=Maze_Frame_sb_y.set)
    Maze_Frame_sb_y.config(command=Maze_Area.yview)
    Maze_Area.pack()
    
    Control_list.append(Maze_Frame_sb_x)
    Control_list.append(Maze_Frame_sb_y)
    Control_list.append(Maze_Area)
    Control_list.append(Maze_Frame)

    for a in range(counter_.shape[0]):      #数据解析
        for b in range(counter_.shape[1]):
            if counter_[a][b]==1:   #数据解析
                counter_[a][b]=0
            elif counter_[a][b]==2: #数据解析
                counter_[a][b]=1
    
    counter=counter_.copy()
    B=init_B(counter)
    counter=counter_.copy()

    for a in range(counter.shape[0]):
        for b in range(counter.shape[1]):
            if type(B[a][b])==Block : #周围方块以及起点和终点不更新
                B[a][b].image = Maze_Area.create_image(size_*a+15, size_*b+15, image=MCBLOCK[counter[a][b]%2]) #颜色更新一次

            elif type(B[a][b])==Block_start:
                B[a][b].image = Maze_Area.create_image(size_*a+15, size_*b+15, image=MCBLOCK_start)

            elif type(B[a][b])==Block_end:
                B[a][b].image = Maze_Area.create_image(size_*a+15, size_*b+15, image=MCBLOCK_end)
    
    top.update_idletasks()

    main_loop(flag=False)

def destroy_all(list_):   #删除构件
    for i in range(len(list_)):
        item=list_.pop()
        #t=threading.Thread(target=item.destroy)
        #t.start()
        
        try:
           # item.destroy()
           pass
        except:
            pass
    
def refresh_windows(Maze_size_length_input=Spinbox(),Maze_size_height_input=Spinbox()):   #刷新界面
    global width_g,height_g,width_min,width_max,height_min,height_max,top,Control_list,Block_list,size_,size_w,size_h,Error_catch
    top.update_idletasks()
    start_time=datetime.datetime.now()
    try:
        width_temp=int(Maze_size_length_input.get())
        height_temp=int(Maze_size_height_input.get())
        
    except:
        try:
            Error_catch.destroy()
        except:
            pass

        Error_catch = Toplevel()
        Error_catch.config(bg='white')
        Error_catch.geometry('440x80'+'+'+str(top.winfo_x()+200)+'+'+str(top.winfo_y()+100))
        Label_notice=Label(Error_catch,font='Times',bg='white',text='错误的输入！请输入数字！')
        Button_notice=Button(Error_catch,font='Times',bg='White',text='知道了！',command=lambda:Error_catch.destroy())
        Label_notice.pack()
        Button_notice.pack()
        Add_logs('[Server]:Failed to refresh the maze!')
        return

    if width_temp<width_min or width_temp>width_max or height_temp<height_min or height_temp>height_max:
        try:
            Error_catch.destroy()
        except:
            pass

        Error_catch = Toplevel()
        Error_catch.config(bg='white')
        Error_catch.geometry('440x80'+'+'+str(top.winfo_x()+200)+'+'+str(top.winfo_y()+100))
        Error_catch.title='出错啦！'
        Label_notice=Label(Error_catch,font='Times',bg='white',text='请输入在宽度在'+str(width_min)+'~'+str(width_max)+'范围内，高度在'+str(height_min)+'~'+str(height_max)+'范围内的数值！')
        Label_notice.pack()
        Button_notice=Button(Error_catch,font='Times',bg='White',text='知道了！',command=lambda:Error_catch.destroy())
        Button_notice.pack()
        Add_logs('[Server]:Failed to refresh the maze!')
        return

    #forget_all(Block_list)

    width_g = width_temp
    height_g = height_temp
    
    #destroy_all(Control_list)
    end_time=datetime.datetime.now()

    main_loop()

def popmenu(event):
    global event_x,event_y,top,Menu_control
    event_x = event.x_root - top.winfo_x() + size_*counter.shape[0]*Maze_Frame_sb_x.get()[0]
    event_y = event.y_root - top.winfo_y() + size_*counter.shape[1]*Maze_Frame_sb_y.get()[0]


    if event_x<=counter.shape[0]*size_ and event_y<=counter.shape[1]*size_:
        Menu_control.post(int(event_x + top.winfo_x() - size_*counter.shape[0]*Maze_Frame_sb_x.get()[0]), int(event_y + top.winfo_y() - size_*counter.shape[1]*Maze_Frame_sb_y.get()[0]))

def ConsoleApp():
    global counter,B,Block_list,top,ConsoleApp_address
    start_time=datetime.datetime.now()
    maze_txt_path = os.path.abspath('RecFiles')
    command=str(ConsoleApp_address)+' '+str(width_g)+' '+str(height_g)+' 99 '+str(int(np.min([width_g, height_g])/10))+' '+maze_txt_path+'\\maze.txt'+' 0'
    Add_logs('[Server]:Send command \''+command+'\' to the shell')
    t = multiprocessing.Process(target=subprocess.call, kwargs={'args':command,"creationflags":CREATE_NO_WINDOW})  #调用生成迷宫函数
    t.start()
    t.join()
    load_data('./RecFiles/maze.txt')

    end_time=datetime.datetime.now()
    Add_logs('[Server]:随机生成迷宫花费：'+str(end_time-start_time))

def set_start_end_point(flag_start):
    global B,Block_list

    x=event_x-7  #+修正量
    y=event_y-30  #+修正量

    for i_temp in range(counter.shape[0]):
        if x<(i_temp+1)*size_ and x>=i_temp*size_:
            i=i_temp

    for j_temp in range(counter.shape[1]):
        if y<(j_temp+1)*size_ and y>=j_temp*size_:
            j=j_temp
    
    if type(B[i][j])==Block_borden:
        return

    for i_temp in range(counter.shape[0]):  #找到原来的起点
        for j_temp in range(counter.shape[0]):
            if type(B[i_temp][j_temp])==Block_start and flag_start:

                B[i_temp][j_temp]=Block(width_=size_w,height_=size_h,i_=B[i_temp][j_temp].i,j_=B[i_temp][j_temp].j)
                B[i_temp][j_temp].image = Maze_Area.create_image(size_*i_temp+15, size_*j_temp+15, image=MCBLOCK_road)



            elif type(B[i_temp][j_temp])==Block_end and flag_start==False:

            
                B[i_temp][j_temp]=Block(width_=size_w,height_=size_h,i_=B[i_temp][j_temp].i,j_=B[i_temp][j_temp].j)
                B[i_temp][j_temp].image = Maze_Area.create_image(size_*i_temp+15, size_*j_temp+15, image=MCBLOCK_road)
        
    

    if flag_start:
        B[i][j]=Block_start(width_=size_w,height_=size_h,i_=i,j_=j)

    else :
        B[i][j]=Block_end(width_=size_w,height_=size_h,i_=i,j_=j)

def function_DFS(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-DFS算法->')
    current_maze_keywords='DFS'
    Maze_num_exe = 1

def function_BFS(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-BFS算法->')
    current_maze_keywords='BFS'
    Maze_num_exe = 2

def function_greedy(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-贪婪算法->')
    current_maze_keywords='greedy'
    Maze_num_exe = 7

def function_equal(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-等代价算法->')
    current_maze_keywords='equal'
    Maze_num_exe = 6

def function_A_Ou(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-A*(欧氏)算法->')
    current_maze_keywords='A*_Ou'
    Maze_num_exe = 4

def function_A_Qie(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-A*(切比雪夫)算法->')
    current_maze_keywords='A*_Qie'
    Maze_num_exe = 5

def function_A_Man(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-A*算法(曼哈顿)->')
    current_maze_keywords='A*_Man'
    Maze_num_exe = 3

def function_A_IDA(Button_menu):
    global current_maze_keywords, Maze_num_exe
    Button_menu.config(text='<-IDA*算法->')
    current_maze_keywords='IDA*'
    Maze_num_exe = 8

def Maze_checker():
    global Error_catch, Error_catch_1
    start_status=False
    end_status=False
    for Block_item in B.flatten():  #判断终点和起点是否重合

        if type(Block_item)==Block_start:
            start_status=True

        elif type(Block_item)==Block_end:
            end_status=True

    if start_status==False or end_status==False:  #倘若未同时找到两个时
        try:
            Error_catch_1.destroy()

        except:
            pass

        Error_catch_1 = Toplevel()
        Error_catch_1.config(bg='white')
        Error_catch_1.geometry('440x80'+'+'+str(top.winfo_x()+200)+'+'+str(top.winfo_y()+100))
        Label_notice=Label(Error_catch_1,font='Times',bg='white',text='请设置正确的起点和终点！')
        Button_notice=Button(Error_catch_1,font='Times',bg='White',text='知道了！',command=lambda:Error_catch_1.destroy())
        Label_notice.pack()
        Button_notice.pack()
        return False
    
    else:

        counter_=counter.copy()  #复制一下
        for i in range(counter_.shape[0]):
            for j in range(counter_.shape[1]):
            
                if counter_[i][j]%2 == 0 and type(B[i][j])==Block or type(B[i][j])==Block_borden:   #数据规范化处理
                    counter_[i][j]=1

                elif counter_[i][j]%2 == 1 and type(B[i][j])==Block:
                    counter_[i][j]=2

        counter_=counter_.copy().T

        with open(r'./RecFiles/Maze_temp.txt','w') as file:
            file.write(str(width_g)+' '+str(height_g))
            for i in range(counter_.shape[0]):
                file.write('\n')
                for j in range(counter_.shape[1]):
                    file.write(str(counter_[i][j])+' ')

        maze_path = os.path.abspath('RecFiles')
        command = Algorithm + '\\Maze_2.exe ' + maze_path + '\\Maze_temp.txt ' + maze_path + '\\temp_answer.txt'
        Add_logs('[Server]:Check the maze!')
        
        t = threading.Thread(target=subprocess.call, kwargs={'args':command,"creationflags":CREATE_NO_WINDOW})
        t.start()
        t.join()

        with open('./RecFiles/temp_answer.txt') as f:
            while True:
                line = f.readline().rstrip()

                if line[0:3]=='way':
                    print(line[-2:])
                    if line[-2:]=='-1':
                        Add_logs('[Server]:This maze is not vaild!')
                        try:
                            Error_catch.destroy()
                        except:
                            pass

                        Error_catch = Toplevel()
                        Error_catch.config(bg='white')
                        Error_catch.geometry('440x80'+'+'+str(top.winfo_x()+200)+'+'+str(top.winfo_y()+100))
                        Label_notice=Label(Error_catch,font='Times',bg='white',text='无效的迷宫')
                        Button_notice=Button(Error_catch,font='Times',bg='White',text='知道了！',command=lambda:Error_catch.destroy())
                        Label_notice.pack()
                        Button_notice.pack()
                        
                        return False

                    break

        return True
        

def load_maze():
    global mortal_thread_1,Request_for_update,Thread_symbol, Maze_Viewer

    if Maze_checker():
        save_data()   #先保存数据
    else:
        return

    pl=psutil.pids()
    pid_name=[]
    for pid in pl:
        try:   
            pid_name.append(psutil.Process(pid).name())
        except:
            pass
        
    #检查该进程是否存在
    maze_path = os.path.abspath('Recfiles')
    command = Algorithm + '\\Maze_'+ str(Maze_num_exe) +'.exe ' + maze_path + '\\Maze_for_c.txt ' + maze_path + '\\answer.txt'
    Add_logs('[Server]:Send command '+ command +' to the shell')
    t = threading.Thread(target=subprocess.call, kwargs={"args":command, "creationflags":CREATE_NO_WINDOW})
    t.start()
    cols=0
    t.join()
    save_data()

    if Thread_symbol==False:  #若第一次调用此函数
        # mortal_Process_1=multiprocessing.Process(target=Socket_communication) #开启服务器
        # mortal_Process_1.start()
        mortal_thread_1=threading.Thread(target=Socket_communication)
        mortal_thread_1.start()
        Thread_symbol=True


    
    if 'MazeViewer.exe' not in pid_name and MazeViewerVail:

        try:
            command=str(Maze_Viewer)
            Process_temp=threading.Thread(target=subprocess.call,kwargs={'args':command,"creationflags":CREATE_NO_WINDOW})  #如果进程不存在则启动exe
            Process_temp.start()
            Add_logs(command)

        except:
            Add_logs('[Server]:Failed to launch the MazeViewer.exe')
            return 

    else:

        Request_for_update=True  #生成更新请求
        Add_logs('[Server]:Request for update')

    Build_Minecraft_Maze(B)

def Socket_communication():
    global Request_for_update
    context = zmq.Context()
    server = context.socket(zmq.PUSH)
    maze_path = os.path.abspath('./RecFiles/Maze_for_c.txt')
    answer_path = os.path.abspath('./RecFiles/answer.txt')
    Add_logs("[Socket_Info]:Socket Online!")
    try:
        with open('./Configs/Config.json','r') as f:
            Config_dict = json.loads(f.read())   #读入配置文件
            address=Config_dict['MazeEditorAddress'][1:]
            #maze_path=Config_dict['mazePath'][:]
            #answer_path=Config_dict['mazePath'][:]
    except:
        address = ('tcp://127.0.0.1:25565')  #默认端口

    Add_logs('[Socket_Info]:Server bind the address '+address)
    Add_logs('[Socket_Info]:Server load the maze from '+maze_path)
    Add_logs('[Socket_Info]:Server load the answer from '+answer_path)
    server.bind(address)

    while True:
        time.sleep(1)
        if Request_for_update:

            msg1 = 'maze_path '+str(maze_path)
            Add_logs('[Socket_Info]:Send maze path '+msg1)
            server.send_string(msg1)

            msg2 = 'answer_path '+str(answer_path)
            Add_logs('[Socket_Info]:Send answer path '+msg2)
            server.send_string(msg2)

            msg = 'update'
            Add_logs('[Socket_Info]:Send update request')
            server.send_string(msg)

            Request_for_update=False

def Build_Minecraft_Maze(B):
    global pos_x, pos_y, length_for_mc, pos_z, width_for_mc, Process_mc, armor_stand
    """check the last maze process"""
    if Process_mc != None:
        Process_mc.terminate()

    count = 0
    
    """Connect to the server."""
    try:
        mc = minecraft.Minecraft.create('47.98.156.203', 7777)    
        mc.setBlocks(pos_x, 0, pos_z, pos_x+length_for_mc, 3, pos_z+width_for_mc, 0)
    except:
        Add_logs('[MC_Warn]:Failed to connect to the Minecraft server!')
        return
        
    """Set the start point"""
    pos_x = 1
    pos_y = 0
    pos_z = 1

    """Get the Maze size"""
    length_for_mc = B.shape[0]   
    width_for_mc = B.shape[1]
    
    """Summon a aromor_stand"""
    try:
        mc.removeEntity(armor_stand)
    except:
        pass

    armor_stand = mc.spawnEntity(0, 0, 0, 30)

    """Generate a plain"""
    mc.setBlocks(pos_x, 0, pos_z, 128, 3, 128, 0)
    mc.setBlocks(pos_x, 0, pos_z, pos_x+length_for_mc-1, 0, pos_z+width_for_mc-1, 2)

    """Set the Maze"""
    
    for i in range(B.shape[0]):
        for j in range(B.shape[1]):
            if type(B[i][j]) == Block_start:
                mc.setBlock(pos_x+i, 0, pos_z+j, 56)
                start_x = pos_x + i
                start_z = pos_z + j
                mc.entity.setPos(armor_stand,pos_x+i+0.5, 2, pos_z+j+0.5)

            elif type(B[i][j]) == Block_end:
                mc.setBlock(pos_x+i, 0, pos_z+j, 57)

            else:

                if counter[i][j]%2 == 0:
                    mc.setBlocks(pos_x+i, 1, pos_z+j, pos_x+i, 2, pos_z+j, 1)

                elif np.random.rand()>0.97:
                    try:
                        id = mc.spawnEntity(pos_x+i, 2 ,pos_z+j, np.random.choice([36,50,5,61], 1))
                        mc.entity.setPos(id, pos_x+i+0.5, 2, pos_z+j+0.5)
                    except:
                        pass

    while True:
        a = np.random.choice(np.arange(B.shape[0]),1)
        b = np.random.choice(np.arange(B.shape[1]),1)
        a = a[0]
        b = b[0]
        if type(B[a][b]) == Block and counter[a][b]%2==1:
            mc.setBlock(pos_x+a, 1, pos_z+b, 37)
            count += 1
        if count==40:
            break

    """Get Players ID And Teleport Them"""
    id_list = mc.getPlayerEntityIds()
    for id in id_list:
        mc.entity.setPos(id, start_x+0.5, 2, start_z+0.5)
    t = threading.Thread(target=set_and_move, kwargs={'mc':mc, 'armor_stand':armor_stand, 'x':pos_x, 'y':pos_y, 'z':pos_z})
    t.start()

    """Post to chat"""
    mc.postToChat('[GameInfo]:The players should collect the flowers nearby while trying to follow the guidance going through the MAZE! Be careful! There would be a plenty of MONSTERS blocking YOU and YOUR TEAMMATES!')

    
def Maze_brush(event):
    global counter, B, size_, x_B, y_B, x_B_last, y_B_last
    x_cur = event.x_root - 4 - top.winfo_x() + size_*counter.shape[0]*Maze_Frame_sb_x.get()[0]
    y_cur = event.y_root - 29 - top.winfo_y() + size_*counter.shape[1]*Maze_Frame_sb_y.get()[0]
    x_B_temp = int(x_cur / size_)
    y_B_temp = int(y_cur / size_)
    if x_B_temp == x_B and y_B_temp == y_B:
        return
    else:
        
        if type(B[x_B_temp][y_B_temp]) == Block:
            if x_B_last == x_B_temp and y_B_last == y_B_temp:
                counter[x_B][y_B] += 1
                B[x_B][y_B].image = Maze_Area.create_image(size_*x_B+15, size_*y_B+15, image=MCBLOCK[counter[x_B][y_B]%2])

            x_B_last = x_B
            y_B_last = y_B
            x_B = x_B_temp
            y_B = y_B_temp
            
            counter[x_B][y_B] += 1
            B[x_B][y_B].image = Maze_Area.create_image(size_*x_B+15, size_*y_B+15, image=MCBLOCK[counter[x_B][y_B]%2])

def Maze_brush_event_click(event):
    
    global click_x, click_y, x_B, y_B
    click_x = event.x_root - 4 - top.winfo_x() 
    click_y = event.y_root - 29 - top.winfo_y() 
    
    if click_x < dx-2 and click_y < dx-2:
        x_cur = event.x_root - 9 - top.winfo_x() + size_*counter.shape[0]*Maze_Frame_sb_x.get()[0]
        y_cur = event.y_root - 29 - top.winfo_y() + size_*counter.shape[1]*Maze_Frame_sb_y.get()[0]
        x_B = int(x_cur / size_)
        y_B = int(y_cur / size_)
        try:
            if type(B[x_B][y_B]) == Block:
                counter[x_B][y_B] += 1
                B[x_B][y_B].image = Maze_Area.create_image(size_*x_B+15, size_*y_B+15, image=MCBLOCK[counter[x_B][y_B]%2])
        except:
            pass
        #print('click_x:'+str(click_x))
        top.bind('<Motion>', Maze_brush)
        # print('click_y:'+str(click_y))

def Maze_brush_event_release(event):
    global release_x, release_y
    release_x = event.x_root - 4 - top.winfo_x()
    release_y = event.y_root- 27 - top.winfo_y()
    # print('release_x:'+str(release_x))
    # print('release_y:'+str(release_y))
    top.unbind('<Motion>')

def Add_logs(log):
    global Logs,logs_text
    try:
        Logs.append(log)
        print(log)
        logs_text.config(state='normal')
        logs_text.insert('end',log+'\n')
        logs_text.config(state='disabled')
    except:
        pass

def ResetTheMaze():
    global counter
    counter=np.zeros((counter.shape[0],counter.shape[1]),dtype=int)
    init_B(counter)
    Add_logs('[Server]:Reset the maze')

def set_and_move(mc,armor_stand,x,y,z):

    cols=0
    with open('./RecFiles/answer.txt') as f:
        while True:
            line = f.readline().rstrip()
            cols += 1
            if line[0:3]=='way':
                break
            if not line:
                Add_logs('[MC]:Failed to load the answer!')
                return
    path = np.loadtxt('./RecFiles/answer.txt',dtype=int,skiprows=cols)     
    for i in range(len(path)):
        step = path[i]
        time.sleep(0.5)
        mc.entity.setPos(armor_stand, x+step[1]+0.5, y+1, z+step[0]+0.5)
        if i != 0 and i != len(path)-1:
            mc.setBlock(x+step[1], y, z+step[0], 41)

def main_loop(flag=True):  #主进程界面
    global width_g,height_g,size_,counter,B,event_x,event_y,Control_list,Block_list,top,Maze_Area,Logs,logs_text
    start_time=datetime.datetime.now()

    Frame_logs = Frame(top, width=400, height=550)
    Frame_logs.place(x=dx+100, y=300)

    logs_text = Text(Frame_logs, width=60, height=30, state='normal')
    logs_sb = Scrollbar(Frame_logs, orient=VERTICAL)
    logs_sb.pack(side=RIGHT, fill=Y)
    logs_sb.config(command=logs_text.yview)
    logs_text.config(yscrollcommand=logs_sb.set)
    logs_text.pack()
    
    Control_list.append(logs_text)
    Control_list.append(logs_sb)
    Control_list.append(Frame_logs)

    for single_log in Logs:
        logs_text.insert('end',single_log+'\n')

    logs_text.config(state='disabled')
    Control_list.append(Frame_logs)
    Control_list.append(logs_sb)
    Control_list.append(logs_text)

    if flag:
        counter=np.zeros([width_g,height_g],dtype=int)     
        B=init_B(counter)

    top.bind("<Button-3>",popmenu)
    top.bind("<Button-1>",Maze_brush_event_click)
    top.bind("<ButtonRelease-1>",Maze_brush_event_release)

    Button_save=Button(top,command=save_data,bg='white',text='保存数据',font='Times',relief=GROOVE)  #保存数据按钮
    Button_save.place(x=dx+100,y=190)
    Control_list.append(Button_save)

    Button_load=Button(top,command=load_data,bg='white',text='导入数据',font='Times',relief=GROOVE) #导入数据按钮 
    Button_load.place(x=dx+200,y=190)
    Control_list.append(Button_load)

    L1=Label(top,text='请设置你的迷宫',font='Times',bg='white')
    L1.place(x=dx+100,y=50)
    Control_list.append(L1)

    L2=Label(top,text='迷宫宽度: ',font='Times',bg='white')
    L2.place(x=dx+100,y=150)
    Control_list.append(L2)

    L3=Label(top,text='迷宫高度: ',font='Times',bg='white')
    L3.place(x=dx+100,y=110)
    Control_list.append(L3)

    L4=Label(top,text='(当前迷宫宽度: '+str(width_g)+')',font='Times',bg='white')
    L4.place(x=dx+285,y=150)
    Control_list.append(L4)

    L5=Label(top,text='(当前迷宫高度: '+str(height_g)+')',font='Times',bg='white')
    L5.place(x=dx+285,y=110)
    Control_list.append(L5)

    L6=Label(top,text='请选择寻路算法:',font='Times',bg='white')
    L6.place(x=dx+100,y=250)
    Control_list.append(L6)

    Maze_size_length_input=Spinbox(top,from_=0,to_=20,width=10)   #迷宫长度输入
    Maze_size_length_input.place(x=dx+200,y=152)
    Control_list.append(Maze_size_length_input)

    Maze_size_height_input=Spinbox(top,from_=0,to_=20,width=10)   #迷宫高度输入
    Maze_size_height_input.place(x=dx+200,y=112)
    Control_list.append(Maze_size_height_input)
    
    Button_refresh=Button(top,command=lambda:refresh_windows(Maze_size_length_input=Maze_size_length_input,Maze_size_height_input=Maze_size_height_input),bg='white',text='更新迷宫',font='Times',relief=GROOVE) #更新界面按钮

    Button_refresh.place(x=dx+300,y=190)
    Control_list.append(Button_refresh)


    Reset_Maze=Button(top,text='重置迷宫',font='Times',bg='white',command=ResetTheMaze,relief=GROOVE)
    Reset_Maze.place(x=dx+500,y=190)
    Control_list.append(Reset_Maze)

    Button_random_spawn_maze=Button(top,bg='white',text='随机生成',font='Times',relief=GROOVE,command=lambda:threading.Thread(target=ConsoleApp).start())  
    Button_random_spawn_maze.place(x=dx+400,y=190)
    Control_list.append(Button_random_spawn_maze)

    Button_menu=Menubutton(top,bg='white',text='<-A*(切比雪夫)算法->',relief=GROOVE,font='Times')
    Button_menu.place(x=dx+245,y=250)

    Button_menu_related=Menu(Button_menu,tearoff=False)
    Button_menu_related.add_command(label='DFS算法',command=lambda:function_DFS(Button_menu))
    Button_menu_related.add_command(label='BFS算法',command=lambda:function_BFS(Button_menu))
    Button_menu_related.add_command(label='贪婪算法',command=lambda:function_greedy(Button_menu))
    Button_menu_related.add_command(label='等代价算法',command=lambda:function_equal(Button_menu))
    Button_menu_related.add_command(label='A*算法(欧式)',command=lambda:function_A_Ou(Button_menu))
    Button_menu_related.add_command(label='A*算法(切比雪夫)',command=lambda:function_A_Qie(Button_menu))
    Button_menu_related.add_command(label='A*算法(曼哈顿)',command=lambda:function_A_Man(Button_menu))
    Button_menu_related.add_command(label='IDA*算法',command=lambda:function_A_IDA(Button_menu))
    Button_menu.config(menu=Button_menu_related,width=20)
    Control_list.append(Button_menu)

    Button_load_config=Button(top,text='开始运行',font='Times',relief=GROOVE,bg='white',command=lambda:threading.Thread(target=load_maze).start())
    Button_load_config.place(x=dx+500,y=245)
    Control_list.append(Button_load_config)

    end_time=datetime.datetime.now()

def main():
    mainloop()

if __name__=='__main__':
    #系统参数
    top = Toplevel()
    CREATE_NO_WINDOW = 0x08000000
    """Maze size"""

    width_min=4
    width_max=128
    height_min=4
    height_max=128
    dx=850
    width_g=22  #迷宫的宽
    height_g=22 #迷宫的高
    Maze_Area = None
    size_=int(dx/width_g)
    size_w=int(dx/width_g)
    size_h=int(dx/width_g)
    ConsoleApp_address = None
    Error_catch = None
    Error_catch_1 = None
    Logs = ['[Server]:Hello']
    logs_text = None  #日志记录框
    Maze_Frame_sb_x = None
    Maze_Frame_sb_y = None
    Abs_path = os.path.abspath('')
    """"""""""""

    event_x=0  #事件发生坐标
    event_y=0
    current_maze_keywords=' '   # 对应关键字对应算法：  DFS->DFS算法   BFS->BFS算法   greedy->贪婪算法   equal->等代价算法   A->A*算法
    Request_for_update=True
    mortal_thread_1=None    #永恒线程_1
    Thread_symbol=False
    Maze_Viewer = None
    x_B = None
    y_B = None
    x_B_last = None
    y_B_last = None

    click_x = None #鼠标左键点击
    click_y = None #鼠标左键点击
    release_x = None #鼠标左键释放
    release_y = None #鼠标左键释放
    Maze_num_exe = 5
    """configs for mc"""

    pos_x=0
    pos_y=0
    pos_z=0
    length_for_mc=0
    width_for_mc=0
    Process_mc=None     #mc进程
    armor_stand = None
    """"""""""""

    try:
        with open('./Configs/Config_Server.json','r') as f:
            Config_dict=json.loads(f.read())   #读入配置文件
            dx = Config_dict['dx']
            width_min = Config_dict['min']
            height_min = Config_dict['min']
            width_max = Config_dict['max']
            height_max = Config_dict['max']
            ConsoleApp_address = Abs_path + Config_dict['ConsoleApp']
            Maze_Viewer = Abs_path + Config_dict['Maze_Viewer']
            MazeViewerVail = Config_dict['MazeViewerVail']
            Algorithm = Abs_path + Config_dict['Algorithm']

    except:
        Add_logs('[Server]:Can not find the Config_Server.json!')
        exit()
    try:
        if dx.lower() == 'default':
            dx = int(top.winfo_screenheight()*3/5)
    except:
        pass

    size_=30
    size_w=30
    size_h=30
    multiprocessing.freeze_support()
    img=PhotoImage(width=1,height=1)
    top.geometry(str(int(top.winfo_screenwidth()))+'x'+str(int(top.winfo_screenheight()))) 
    top.config(bg='white')
    top.resizable(0, 0)
    top.protocol("WM_DELETE_WINDOW", lambda:os._exit(0));
    # background_img = Label(top, width=int(top.winfo_screenwidth()*4/6), height=int(top.winfo_screenheight()*4/6))
    # background_img.config(image=BackGround)
    # background_img.pack()
    top.title('Maze')

    B=np.empty([width_g,height_g],dtype=Block)
    counter=np.zeros([width_g,height_g],dtype=int)
    MCBLOCK=[MCBLOCK_wall, MCBLOCK_road]
    Block_list=[]
    Control_list=[]
    All_list=[]
    Menu_control=Menu(top,tearoff=False)
    Menu_control.add_command(label='起点',command=lambda:set_start_end_point(flag_start=True))
    Menu_control.add_command(label='终点',command=lambda:set_start_end_point(flag_start=False))
    main_loop()
    main()