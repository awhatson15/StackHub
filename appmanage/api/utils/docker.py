import os, io, sys, platform, shutil, time, json, datetime
import re,docker
from api.utils import shell_execute
from api.utils import network

from dotenv import load_dotenv, find_dotenv
import dotenv
from pathlib import Path

def get_process_perc(app_name):
    
    process_now = "0%"
    path = "/data/apps/" + app_name + "/.env"
    app_version_env, app_version = read_env(path, "APP_VERSION")
    print(app_version)
    client = docker.from_env()
    image_name = app_name + ":" + app_version
    print(resp)
    resp = client.api.pull(app_name, tags=app_version, stream=True, decode=True)

    for line in resp:
      print(json.dumps(line, indent=4))

    return process_now

def check_vm_resource():
    # 服务器剩余资源是否足够安装，如cpu，内存，硬盘

    return true

def check_app_directory(app_name):
    # 判断/data/apps/app_name是否已经存在，如果已经存在，方法结束
    print("checking dir...")
    path = "/data/apps/"+app_name
    isexsits = os.path.exists(path)
    return isexsits

def check_app_compose(app_name):
    print("checking port...")
    path = "/data/apps/" + app_name + "/.env"
    http_port = read_env(path, "APP_HTTP_PORT")
    db_port = read_env(path, "APP_DB.*_PORT")
    #1.判断/data/apps/app_name/.env中的port是否占用，没有被占用，方法结束（network.py的get_start_port方法）
    if http_port != "":
        print("check http port...")
        http_port = network.get_start_port(http_port)
        modify_env(path, "APP_HTTP_PORT", http_port)
    if db_port != "":
        print("check db port...")
        db_port = network.get_start_port(db_port)
        modify_env(path, "APP_DB.*_PORT", db_port)
    print("port check complete")
    return

def read_env(path, key):
    output = shell_execute.execute_command_output_all("cat " + path + "|grep "+ key+ "|head -1")
    code = output["code"]
    ret = ""    #the value of environment var
    if int(code) == 0 and output["result"] != "":
        ret = output["result"]
        ret = ret.split("=")[1]
        ret = re.sub("'","",ret)
        ret = re.sub("\n","",ret)
    return ret

def modify_env(path, env_name, value):
    file_data = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if re.match(env_name, line) != None:
                env_name = line.split("=")[0]
                line = line.replace(line, env_name + "=" + value+"\n")
            file_data += line
    with open(path, "w", encoding="utf-8") as f:
        f.write(file_data)
