import os, io, sys, platform, shutil, time, json, datetime
import re,docker,requests
from api.utils import shell_execute
from api.utils import network
import psutil as p
from dotenv import load_dotenv, find_dotenv
import dotenv
from pathlib import Path
from api.utils.common_log import myLogger

def get_process_perc(app_name, real_name):
    
    process_now = "pulling"
    image_name = real_name
    if real_name == "codeserver":
       image_name = "code-server"
    elif real_name == "codeserver2":
       image_name = "code-server2"
    output = shell_execute.execute_command_output_all("sudo docker image list |grep  " + image_name)
    code = output["code"]
    if int(code) == 0 and output["result"] != "":
        process_now = "starting"
    
    output = shell_execute.execute_command_output_all("docker inspect " +  app_name + "|grep error")
    code = output["code"]
    if int(code) == 0 and output["result"] == "":
        process_now = "Initializing"
    
    return process_now

def check_vm_resource(app_name):
    myLogger.info_logger("Checking virtual memory resource ...")
    cpu_count = p.cpu_count()
    mem = p.virtual_memory()
    mem_total = float(mem.total) / 1024 / 1024 / 1024
    requirements_var = read_var(app_name, 'requirements')
    need_cpu_count = int(requirements_var['cpu'])
    need_mem = int(requirements_var['memory'])
    if cpu_count<need_cpu_count or mem_total<need_mem:
        return False

    mem_free = float(mem.available) / 1024 / 1024 / 1024
    if mem_total>=8 and mem_free<=4:
        return False

    need_disk = int(requirements_var['disk'])
    disk = p.disk_usage('/')
    disk_total = float(disk.total) / 1024 / 1024 / 1024
    disk_free = float(disk.free) / 1024 / 1024 / 1024
    if disk_total<need_disk or disk_free<2:
        return False

    return True

def check_app_directory(app_name):
    # websoft9's support applist
    myLogger.info_logger("Checking dir...")
    path = "/data/apps/"+app_name
    isexsits = os.path.exists(path)
    return isexsits

def check_app_compose(app_name):
    myLogger.info_logger("Checking port...")
    path = "/data/apps/" + app_name + "/.env"
    port_dic = read_env(path, "APP_.*_PORT")
    #1.判断/data/apps/app_name/.env中的port是否占用，没有被占用，方法结束（network.py的get_start_port方法）
    for port_name in port_dic:
        port_value = network.get_start_port(port_dic[port_name])
        modify_env(path, port_name, port_value)
    myLogger.info_logger("Port check complete")
    return

def read_env(path, key):
    myLogger.info_logger("Read " + path)
    output = shell_execute.execute_command_output_all("cat " + path + "|grep "+ key)
    code = output["code"]
    env_dic = {}
    if int(code) == 0 and output["result"] != "":
        ret = output["result"]
        env_list = ret.split()
        for env in env_list:
            env_dic[env.split("=")[0]] = env.split("=")[1]
    return env_dic

def modify_env(path, env_name, value):
    myLogger.info_logger("Modify " + path + "...")
    file_data = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if re.match(env_name, line) != None:
                env_name = line.split("=")[0]
                line = line.replace(line, env_name + "=" + value+"\n")
            file_data += line
    with open(path, "w", encoding="utf-8") as f:
        myLogger.info_logger("Modify " + path + ": Change " + env_name + " to " + value)
        f.write(file_data)

def read_var(app_name, var_name):
    value = "-"
    var_path = "/data/apps/" + app_name + "/variables.json"
    myLogger.info_logger("Read " + var_path)
    try:
        f = open(var_path, 'r', encoding='utf-8')
        var = json.load(f)
        try:
            value = var[var_name]
        except KeyError:
            myLogger.warning_logger("Read " + var_path + ": No key " + var_name)
    except FileNotFoundError:
        myLogger.warning_logger(var_path + " not found")
    return value
