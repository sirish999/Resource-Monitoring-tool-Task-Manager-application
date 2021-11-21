#!/usr/bin/env python
import os
import pwd
import heapq
import time
import tkinter
from tkinter import *
import tkinter.ttk
import sys

import warnings

warnings.filterwarnings("ignore")
global sleep_time
sleep_time = 1000 * 2  # sleep time in the form of sleep

previous_data_trans = 0
speed=0
previous_ctxt = previous_intr = 0
cpu_prev = 0


previous_block_read =0
previous_block_write = 0
previous_disk_read = 0
previous_disk_write = 0

top_process = 20  # top processes to display

previous_free_mem = 0
previous_utime = 0
previous_systime = 0
previous_idle = 0
cpu={}

class Task_Manager:

    def get_cpu_ctxt_intr_utilization(self):
        global previous_utime, previous_systime, previous_idle
        global previous_ctxt, previous_intr
        total_cpu = 0
        with open("/proc/stat", "r") as f:
            file = f.readlines()
            for line in file:
                columns = line.split()

                if "cpu" in columns[0]:
                    total_cpu += 1
                if "cpu" == columns[0]:
                    current_utime = float(columns[1])
                    current_systime = float(columns[3])
                    current_idle = float(columns[4])

                    utilization_user_time = current_utime - previous_utime
                    utilization_sys_time = current_systime - previous_systime
                    utilization_cpu_time = utilization_user_time + utilization_sys_time + current_idle - previous_idle

                    total_utilization = ((utilization_user_time + utilization_sys_time) / (utilization_cpu_time)) * 100

                    previous_idle = current_idle
                    previous_utime = current_utime
                    previous_systime = current_systime

                elif "ctxt" == columns[0]:
                    current_ctxt = int(columns[1])
                    total_ctxt = (current_ctxt - previous_ctxt)
                    previous_ctxt = current_ctxt

                elif "intr" == columns[0]:
                    current_intr = int(columns[1])
                    total_intr = current_intr - previous_intr
                    previous_intr = current_intr


        self.cpu_info = [str(total_cpu - 1), str(round(total_utilization, 2)), str(int(total_intr /2)),
                         str(int(total_ctxt /2))]


    #--------------------------------------------------------------------------------------------------------------------------------------------------------

    def get_mem_utilization(self):
        total_mem = 0
        global previous_free_mem
        with open("/proc/meminfo", "r") as f:
            file = f.readlines()
            for ptr, line in enumerate(file):
                columns = line.split()
                if ptr == 0:
                    total_mem = float(columns[1]) / (1024 * 1024)  # KB to GB
                if ptr == 1:
                    current_free_mem = float(columns[1])
                    break
        avg_mem_free = ((current_free_mem + previous_free_mem) / 2) / (1024 * 1024)  # KB to GB       # gauge value because it is average.
        mem_utilization = ((total_mem - avg_mem_free) / total_mem) * 100
        previous_free_mem = current_free_mem

        self.mem_info = [str(round(total_mem, 2)), str(round(avg_mem_free, 2)), str(round(mem_utilization, 2))]


    #--------------------------------------------------------------------------------------------------------------------------------------------------------

    def get_disk_stat(self):

        count = 0
        global previous_block_read, previous_block_write, previous_disk_read, previous_disk_write
        with open("/proc/diskstats", "r") as f:
            file = f.readlines()
            for ptr, line in enumerate(file):
                columns = line.split()
                if columns[2] == "sda":

                    current_disk_read = float(columns[3])
                    current_disk_write = float(columns[7])

                    current_block_read = float(columns[5])
                    current_block_write = float(columns[9])

                    disk_utilization = (((current_block_read + current_block_write - previous_block_read - previous_block_write) / 2) * 512) / (10 ** 6)

                    disk_read = ((current_disk_read - previous_disk_read) / 2)
                    disk_write = ((current_disk_write - previous_disk_write) / 2)
                    block_read = ((current_block_read - previous_block_read) / 2)
                    block_write = ((current_block_write - previous_block_write) / 2)


                    previous_disk_write = current_disk_write
                    previous_disk_read = current_disk_read
                    previous_block_write = current_block_write
                    previous_block_read = current_block_read

        self.disk_info = [str(count - 1), str(round(disk_utilization, 2)), str(disk_read), str(disk_write), str(block_read),
                          str(block_write)]


    #--------------------------------------------------------------------------------------------------------------------------------------------------------

    def get_net_utilization(self):
        global previous_data_trans
        global speed
        with open("/proc/net/dev") as f:
            device = []
            one_pass = 1
            for lines in f.readlines():
                if one_pass > 2:

                    data = lines.split()

                    if "lo" in data[0]:
                        pass
                    else:
                        device.append(data[0].split(":")[0])

                        current_data_trans = float(data[1]) + float(data[9])
                        with open("/sys/class/net/enp0s3/speed") as f:
                            speed=f.read()
                else:
                    one_pass += 1


        net_utilization = float(((current_data_trans - previous_data_trans) / 2))
        net_utilization = (net_utilization*8)/(1000*1000)
        net_utilization = net_utilization/(int(speed))

        previous_data_trans = current_data_trans

        self.net_info = [str(round(net_utilization, 2))]  # speed of network
        
                                

    #--------------------------------------------------------------------------------------------------------------------------------------------------------

    def get_net_tcp_udp(self):  
        def compare_inode(inode, local_address, loc_socket, remote_address, remote_socket, c_type, uid, l1):
            for file in os.listdir("/proc"):
                if file.isdigit():
                    try:
                        path = "/proc/" + str(file) + "/fd"

                        for fd_files in os.listdir(path):
                            socket = os.stat(path + "/" + fd_files).st_ino

                            if (socket == inode):
                                with open("/proc/" + str(file) + "/comm") as file_pname:
                                    p_name = file_pname.readlines()[0].split("\n")[0]

                                user_name = pwd.getpwuid(uid).pw_name
                                loc_list = [c_type, local_address, loc_socket, remote_address, loc_socket,
                                            remote_address, remote_socket, user_name, p_name]
                                l1.append(loc_list)

                    except Exception as e:
                        pass

        def convert_to_ip(s):

            bytes_b = ["".join(x) for x in zip(*[iter(s)] * 2)]
            bytes_b = [int(x, 16) for x in bytes_b]
            return ".".join(str(x) for x in reversed(bytes_b))

        def port(s):
            return str(int(s, 16))

        self.connection_info = list()
        self.connection_info2 = list()
        with open("/proc/net/tcp", "r") as f:
            start_read = False
            for line in f.readlines():
                if start_read == False:
                    start_read = True
                else:
                    field = line.split()

                    local_address = convert_to_ip(field[1].split(":")[0])
                    remote_address = convert_to_ip(field[2].split(":")[0])
                    loc_socket = port(field[1].split(":")[1])
                    remote_socket = port(field[2].split(":")[1])
                    inode = int(field[9])
                    uid = int(field[7])

                    compare_inode(inode, local_address, loc_socket, remote_address, remote_socket, "tcp", uid,
                                  self.connection_info)

        with open("/proc/net/snmp", "r") as f2:
            lines = []
            for line in f2.readlines():
                lines.append(line.split())
            tcpinfo = []

            tcp_active_open = lines[5][5]
            tcp_current_estab = lines[5][9]

            tcpinfo.append(tcp_active_open)
            tcpinfo.append(tcp_current_estab)

            self.connection_info2.append(tcpinfo)




    #--------------------------------------------------------------------------------------------------------------------------------------------------------

    def get_per_process_data(self):
        global top_process, cpu_prev

        with open('/proc/stat') as cf:
            data_cpu = cf.readlines()
            for line in data_cpu:
                total_memory = float(line.strip().split()[1:2][0])
                break

        def get_names(pid):

            try:
                with open("/proc/" + str(pid) + "/comm", "r") as file_pname:
                    pname = file_pname.readlines()[0].split("\n")[0]

                with open("/proc/" + str(pid) + "/status", "r") as file_uid:
                    data = file_uid.readlines()
                    for line in data:
                        columns = line.split("\t")
                        if columns[0] == "Uid:":
                            uid = columns[1]
                            uname = pwd.getpwuid(int(uid)).pw_name
                            break

                return uname, pname

            except Exception as e:
                pass

        def get_vmsize(path):

            path = path + "/status"
            with open(path, "r") as file:
                data = file.readlines()

                vm_size = float(data[17].split(":")[1].split()[0])

                return vm_size

        def heappush(h, item, key=lambda x: x[3]):
            heapq.heappush(h, (key(item), item))

        for_one_pass = True
        need_vm = True
        per_process_info = list()
        heapq.heapify(per_process_info)

        with open('/proc/stat', "r") as cf:
            data_cpu = cf.readlines()
            field = list()
            for line in data_cpu:
                field = line.split()[1:]
                break
            total_cpu = float(field[0]) + float(field[2]) + float(field[3])
            if not for_one_pass:
                diff = total_cpu - cpu_prev
            cpu_prev = total_cpu


        for p_id in os.listdir("/proc"):
            if p_id.isdigit():
                try:
                    path_stat = "/proc/" + str(p_id) + "/stat"

                    if need_vm == True:
                        vmsize = get_vmsize("/proc/" + str(p_id))
                        need_vm = False

                    with open(path_stat) as f:
                        data = f.readlines()[0].split()
                        p_cpu = float(data[13]) + float(data[14])  # jiffy

                        p_vm = float(data[22]) / (1024 * 1024)
                        p_mem = (float(data[23]) * 4) / (1024)


                        p_uname, p_pname = get_names(p_id)
                        if not p_uname:
                            break


                        p_cpu_utilization = (p_cpu / total_cpu) * 100  # percentage


                        l = [str(p_id), str(p_uname), str(p_pname), str(round(p_cpu_utilization, 2)), str(round(p_mem, 2)),
                             str(round(p_vm, 2))]

                        heappush(per_process_info, l)
                        # print("heaped")

                except Exception as e:
                    print(e)
                    # pass

        self.processes_list = heapq.nlargest(top_process, per_process_info)



#-----------------------------------------------------------------------------------------------------------------
    def keylogger(self):
        import os

        #path="/home/sirish/Documents/logger6/test.txt"

        def display():
            f = open("/home/sirish/Documents/logger6/test", 'r')
            self.file_contents = f.read()
            f.close()
        #insert()
        #remove()

        display()





#-----------------------------------------------------------------------------------------------------------------

s = Task_Manager()

r = tkinter.Tk()
r.title("Task Manager")
r.geometry("1500x1000")
note = tkinter.ttk.Notebook(r)
note.grid(row=1, column=0, rowspan=100, columnspan=300)

frame1 = tkinter.ttk.Frame(note)
frame2 = tkinter.ttk.Frame(note)
frame3 = tkinter.ttk.Frame(note)
frame4 = tkinter.ttk.Frame(note)
frame5 = tkinter.ttk.Frame(note)

note.add(frame1, text="CPU")
note.add(frame2, text="DISK")
note.add(frame3, text="TCP CONNECTIONS")
note.add(frame4, text="PROCESSES")
note.add(frame5, text="KEYLOGGER")


tb1 = Text(frame1)
tb1.grid(row=1, column=0, rowspan=100, columnspan=300)

tb2 = Text(frame2)
tb2.grid(row=1, column=0, rowspan=100, columnspan=300)

tb3 = Text(frame3)
tb3.grid(row=1, column=0, rowspan=100, columnspan=300)

tb4 = Text(frame4)
tb4.grid(row=1, column=0, rowspan=100, columnspan=300)

tb5 = Text(frame5)
tb5.grid(row=1, column=0, rowspan=100, columnspan=300)








def display_cpu_mem_net():
    s.get_cpu_ctxt_intr_utilization()
    s.get_mem_utilization()
    s.get_net_utilization()

    tb1.delete('1.0', END)
    tb1.insert(END, "Number of CPUs\t\t\t" + "CPU usage (%)\t\t" + "\n")
    tb1.insert(END,  s.cpu_info[0] + '\t\t\t' + s.cpu_info[1] + '\n\n')
    tb1.insert(END, "--------------------------------------------------------\n")

    tb1.insert(END, "Number of Interrupts per second        :\t\t")
    tb1.insert(END, s.cpu_info[2] + '\n\n')

    tb1.insert(END, "Number of Context switches per second  :\t\t")
    tb1.insert(END, s.cpu_info[3] + '\t' + '\n\n')
    tb1.insert(END, "--------------------------------------------------------\n")

    tb1.insert(END, "Total_Memory(GB)\t\t\t" + "Free_Mem(GB)\t\t" + "Mem_utilization %\t\t" + "\n")
    tb1.insert(END, s.mem_info[0] + "\t\t\t" + s.mem_info[1] + "\t\t" + s.mem_info[2] + '\n\n')
    tb1.insert(END, "--------------------------------------------------------\n")

    tb1.insert(END, "Network_utilization (%) \t\t\n")
    tb1.insert(END, s.net_info[0] + '\n')

    s.net_info = list()
    s.cpu_info = list()
    s.mem_info = list()
    r.after(sleep_time, display_cpu_mem_net)


def display_disk_utilization():
    s.get_disk_stat()
    tb2.delete('1.0', END)
    tb2.insert(END, "Disk utilization (%)" + '\n')
    tb2.insert(END, s.disk_info[1] + '\n\n')

    tb2.insert(END, "Disk Reads/s\t\t" + "Disk Writes/s" + '\n')
    tb2.insert(END, s.disk_info[2] + "\t\t" + s.disk_info[3] + '\n\n')

    tb2.insert(END, "Block Reads/s" + "\t\t" + "Block Writes/s" + '\n')
    tb2.insert(END, s.disk_info[4] + "\t\t" + s.disk_info[5] + '\n\n')
    # tb2.insert(END,"########################################################\n\n")
    s.disk_info = list()
    r.after(sleep_time, display_disk_utilization)


def display_tcp():
    s.get_net_tcp_udp()
    tb3.delete('1.0', END)
    tb3.insert(END, "User_Name\t\t" + "Program\t\t" + "Source Address\t\t\t" + "Remote Address\t\t" + "\n")
    for f in s.connection_info:
        tb3.insert(END, f[7] + '\t\t' + f[8] + '\t\t' + f[1] + ":" + f[2] + '\t\t\t' + f[3] + ":" + f[4] + '\n')
    tb3.insert(END, '\n')

    for f in s.connection_info2:
        tb3.insert(END,'Active TCP connections\t\t:'+ f[0] + '\t'+'\n'+'Current esablished TCP connections\t\t:' + f[1]  + '\t\t' + '\n')
    s.connection_info = list()
    s.connection_info2 = list()
    r.after(sleep_time, display_tcp)


def display_processes():

    s.get_per_process_data()
    tb4.delete('1.0', END)
    tb4.insert(END, "PID\t" + "Name\t\t" + "User\t" + "CPU(%)\t" + "Memory(MB)\t\t" + "Virtual Memory(MB)" + "\n")
    for p in s.processes_list:
        tb4.insert(END, p[1][0] + "\t" + p[1][2] + "\t\t" + p[1][1] + "\t" + p[1][3] + "\t" + p[1][4] + "\t\t" + p[1][
            5] + "\n")
    s.processes_list = list()
    r.after(sleep_time, display_processes)

def keylogger():

    s.keylogger()
    tb5.delete('1.0', END)

    def insert():
        #os.system('sudo -i')


        os.system('insmod /home/sirish/Documents/logger6/checkc6.ko')
        #os.system('insmod ')

    def remove():
        #os.system('sudo -i')


        #os.system('cd /home/sirish/Documents/logger6')
        os.system('rmmod checkc6')
        f = open('/home/sirish/Documents/logger6/test', 'w')
        f.close()
    def clear():
        f = open('/home/sirish/Documents/logger6/test', 'w')
        f.close()

    inserts = tkinter.Button(frame5, text="Keylogger: ON ", command=insert)
    removes = tkinter.Button(frame5, text="Keylogger: OFF ", command=remove)
    clear = tkinter.Button(frame5, text="Clear contents of Keylogger file", command=clear)

    inserts.grid(row=2, column=1)#can not use grid and pack at the same time. Only use one
    removes.grid(row=2, column=50)
    clear.grid(row=3, column=50)

    tb5.insert(END, '\n\n\n\n')
    #tb5.insert(END, 'Keylogger File:\n------------------------------------------------------------\n')
    tb5.insert(END, s.file_contents)
    #Stb5.insert(END, '\n------------------------------------------------------------\n')


    r.after(sleep_time, keylogger)


display_cpu_mem_net()
display_disk_utilization()
display_tcp()
display_processes()
keylogger()
r.mainloop()