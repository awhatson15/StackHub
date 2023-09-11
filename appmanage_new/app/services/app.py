# # 合并applist
# def conbine_list(installing_list, installed_list):
#     app_list = installing_list + installed_list
#     result_list = []
#     appid_list = []
#     for app in app_list:
#         app_id = app['app_id']
#         if app_id in appid_list:
#             continue
#         else:
#             appid_list.append(app_id)
#             result_list.append(app)
#     return result_list

# # 获取所有app的信息
# def get_my_app(app_id):
#     installed_list = get_apps_from_compose()
#     installing_list = get_apps_from_queue()

#     app_list = conbine_list(installing_list, installed_list)
#     find = False
#     ret = {}
#     if app_id != None:
#         for app in app_list:
#             if app_id == app['app_id']:
#                 ret = app
#                 find = True
#                 break
#         if not find:
#             raise CommandException(const.ERROR_CLIENT_PARAM_NOTEXIST, "This App doesn't exist!", "")
#     else:
#         ret = app_list
#     myLogger.info_logger("app list result ok")
#     return ret

# def get_apps_from_compose():
#     myLogger.info_logger("Search all of apps ...")
#     cmd = "docker compose ls -a --format json"
#     output = shell_execute.execute_command_output_all(cmd)
#     output_list = json.loads(output["result"])
#     myLogger.info_logger(len(output_list))
#     ip = "localhost"
#     try:
#         ip_result = shell_execute.execute_command_output_all("cat /data/apps/w9services/w9appmanage/public_ip")
#         ip = ip_result["result"].rstrip('\n')
#     except Exception:
#         ip = "127.0.0.1"

#     app_list = []
#     for app_info in output_list:
#         volume = app_info["ConfigFiles"]
#         app_path = volume.rsplit('/', 1)[0]
#         customer_name = volume.split('/')[-2]
#         app_id = ""
#         app_name = ""
#         trade_mark = ""
#         port = 0
#         url = ""
#         admin_url = ""
#         image_url = ""
#         user_name = ""
#         password = ""
#         official_app = False
#         app_version = ""
#         create_time = ""
#         volume_data = ""
#         config_path = app_path
#         app_https = False
#         app_replace_url = False
#         default_domain = ""
#         admin_path = ""
#         admin_domain_url = ""
#         if customer_name in ['w9appmanage', 'w9nginxproxymanager', 'w9redis', 'w9kopia',
#                              'w9portainer'] or app_path == '/data/apps/w9services/' + customer_name:
#             continue

#         var_path = app_path + "/variables.json"
#         official_app = check_if_official_app(var_path)

#         status_show = app_info["Status"]
#         status = app_info["Status"].split("(")[0]
#         if status == "running" or status == "exited" or status == "restarting":
#             if "exited" in status_show and "running" in status_show:
#                 if status == "exited":
#                     cmd = "docker ps -a  -f name=" + customer_name + " --format {{.Names}}#{{.Status}}|grep Exited"
#                     result = shell_execute.execute_command_output_all(cmd)["result"].rstrip('\n')
#                     container = result.split("#Exited")[0]
#                     if container != customer_name:
#                         status = "running"
#             if "restarting" in status_show:
#                 about_time = get_createtime(official_app, app_path, customer_name)
#                 if "seconds" in about_time:
#                     status = "restarting"
#                 else:
#                     status = "failed"
#         elif status == "created":
#             status = "failed"
#         else:
#             continue

#         if official_app:
#             app_name = docker.read_var(var_path, 'name')
#             app_id = app_name + "_" + customer_name  # app_id
#             # get trade_mark
#             trade_mark = docker.read_var(var_path, 'trademark')
#             image_url = get_Image_url(app_name)
#             # get env info
#             path = app_path + "/.env"
#             env_map = docker.get_map(path)

#             try:
#                 myLogger.info_logger("get domain for APP_URL")
#                 domain = env_map.get("APP_URL")
#                 if "appname.example.com" in domain or ip in domain:
#                     default_domain = ""
#                 else:
#                     default_domain = domain
#             except Exception:
#                 myLogger.info_logger("domain exception")
#             try:
#                 app_version = env_map.get("APP_VERSION")
#                 volume_data = "/data/apps/" + customer_name + "/data"
#                 user_name = env_map.get("APP_USER", "")
#                 password = env_map.get("POWER_PASSWORD", "")
#                 admin_path = env_map.get("APP_ADMIN_PATH")
#                 if admin_path:
#                     myLogger.info_logger(admin_path)
#                     admin_path = admin_path.replace("\"", "")
#                 else:
#                     admin_path = ""

#                 if default_domain != "" and admin_path != "":
#                     admin_domain_url = "http://" + default_domain + admin_path
#             except Exception:
#                 myLogger.info_logger("APP_USER POWER_PASSWORD exception")
#             try:
#                 replace = env_map.get("APP_URL_REPLACE", "false")
#                 myLogger.info_logger("replace=" + replace)
#                 if replace == "true":
#                     app_replace_url = True
#                 https = env_map.get("APP_HTTPS_ACCESS", "false")
#                 if https == "true":
#                     app_https = True
#             except Exception:
#                 myLogger.info_logger("APP_HTTPS_ACCESS exception")

#             try:
#                 http_port = env_map.get("APP_HTTP_PORT", "0")
#                 if http_port:
#                     port = int(http_port)
#             except Exception:
#                 pass
#             if port != 0:
#                 try:
#                     if app_https:
#                         easy_url = "https://" + ip + ":" + str(port)
#                     else:
#                         easy_url = "http://" + ip + ":" + str(port)
#                     url = easy_url
#                     admin_url = get_admin_url(customer_name, url)
#                 except Exception:
#                     pass
#             else:
#                 try:
#                     db_port = list(docker.read_env(path, "APP_DB.*_PORT").values())[0]
#                     port = int(db_port)
#                 except Exception:
#                     pass
#         else:
#             app_name = customer_name
#             app_id = customer_name + "_" + customer_name
#         create_time = get_createtime(official_app, app_path, customer_name)
#         if status in ['running', 'exited']:
#             config = Config(port=port, compose_file=volume, url=url, admin_url=admin_url,
#                             admin_domain_url=admin_domain_url,
#                             admin_path=admin_path, admin_username=user_name, admin_password=password,
#                             default_domain=default_domain)
#         else:
#             config = None
#         if status == "failed":
#             status_reason = StatusReason(Code=const.ERROR_SERVER_SYSTEM, Message="system original error",
#                                          Detail="unknown error")
#         else:
#             status_reason = None
#         app = App(app_id=app_id, app_name=app_name, customer_name=customer_name, trade_mark=trade_mark,
#                   app_version=app_version, create_time=create_time, volume_data=volume_data, config_path=config_path,
#                   status=status, status_reason=status_reason, official_app=official_app, image_url=image_url,
#                   app_https=app_https, app_replace_url=app_replace_url, config=config)

#         app_list.append(app.dict())
#     return app_list

# # 安装
# def install_app(app_name, customer_name, app_version):
#     myLogger.info_logger("Install app ...")
#     ret = {}
#     ret['ResponseData'] = {}
#     app_id = app_name + "_" + customer_name
#     ret['ResponseData']['app_id'] = app_id

#     code, message = check_app(app_name, customer_name, app_version)
#     if code == None:
#         q.enqueue(install_app_delay, app_name, customer_name, app_version, job_id=app_id)
#     else:
#         ret['Error'] = get_error_info(code, message, "")

#     return ret

#     def start_app(app_id):
#     info, flag = app_exits_in_docker(app_id)
#     if flag:
#         app_path = info.split()[-1].rsplit('/', 1)[0]
#         cmd = "docker compose -f " + app_path + "/docker-compose.yml start"
#         shell_execute.execute_command_output_all(cmd)
#     else:
#         raise CommandException(const.ERROR_CLIENT_PARAM_NOTEXIST, "APP is not exist", "")


# def stop_app(app_id):
#     info, flag = app_exits_in_docker(app_id)
#     if flag:
#         app_path = info.split()[-1].rsplit('/', 1)[0]
#         cmd = "docker compose -f " + app_path + "/docker-compose.yml stop"
#         shell_execute.execute_command_output_all(cmd)
#     else:
#         raise CommandException(const.ERROR_CLIENT_PARAM_NOTEXIST, "APP is not exist", "")


# def restart_app(app_id):
#     code, message = docker.check_app_id(app_id)
#     if code == None:
#         info, flag = app_exits_in_docker(app_id)
#         if flag:
#             app_path = info.split()[-1].rsplit('/', 1)[0]
#             cmd = "docker compose -f " + app_path + "/docker-compose.yml restart"
#             shell_execute.execute_command_output_all(cmd)
#         else:
#             raise CommandException(const.ERROR_CLIENT_PARAM_NOTEXIST, "APP is not exist", "")
#     else:
#         raise CommandException(code, message, "")

# def uninstall_app(app_id):
#     app_name = app_id.split('_')[0]
#     customer_name = app_id.split('_')[1]
#     app_path = ""
#     info, code_exist = app_exits_in_docker(app_id)
#     if code_exist:
#         app_path = info.split()[-1].rsplit('/', 1)[0]
#         cmd = "docker compose -f " + app_path + "/docker-compose.yml down -v"
#         lib_path = '/data/library/apps/' + app_name
#         if app_path != lib_path:
#             cmd = cmd + " && sudo rm -rf " + app_path
#         shell_execute.execute_command_output_all(cmd)
#     else:
#         if check_app_rq(app_id):
#             delete_app_failedjob(app_id)
#         else:
#             raise CommandException(const.ERROR_CLIENT_PARAM_NOTEXIST, "AppID is not exist", "")
#     # Force to delete docker compose
#     try:
#         cmd = " sudo rm -rf /data/apps/" + customer_name
#         shell_execute.execute_command_output_all(cmd)
#     except CommandException as ce:
#         myLogger.info_logger("Delete app compose exception")
#     # Delete proxy config when uninstall app
#     app_proxy_delete(app_id)


# # 安装失败后的处理
# def delete_app(app_id):
#     try:
#         app_name = app_id.split('_')[0]
#         customer_name = app_id.split('_')[1]
#         app_path = ""
#         info, code_exist = app_exits_in_docker(app_id)
#         if code_exist:
#             app_path = info.split()[-1].rsplit('/', 1)[0]
#             cmd = "docker compose -f " + app_path + "/docker-compose.yml down -v"
#             lib_path = '/data/library/apps/' + app_name
#             if app_path != lib_path:
#                 cmd = cmd + " && sudo rm -rf " + app_path
#             try:
#                 myLogger.info_logger("Intall fail, down app and delete files")
#                 shell_execute.execute_command_output_all(cmd)
#             except Exception:
#                 myLogger.info_logger("Delete app compose exception")
#             # 强制删除失败又无法通过docker compose down 删除的容器
#             try:
#                 myLogger.info_logger("IF delete fail, force to delete containers")
#                 force_cmd = "docker rm -f $(docker ps -f name=^" + customer_name + " -aq)"
#                 shell_execute.execute_command_output_all(force_cmd)
#             except Exception:
#                 myLogger.info_logger("force delete app compose exception")

#         else:
#             if check_app_rq(app_id):
#                 delete_app_failedjob(app_id)
#             else:
#                 raise CommandException(const.ERROR_CLIENT_PARAM_NOTEXIST, "AppID is not exist", "")
#         cmd = " sudo rm -rf /data/apps/" + customer_name
#         shell_execute.execute_command_output_all(cmd)
#     except CommandException as ce:
#         myLogger.info_logger("Delete app compose exception")

# #安装准备
# def prepare_app(app_name, customer_name):
#     library_path = "/data/library/apps/" + app_name
#     install_path = "/data/apps/" + customer_name
#     shell_execute.execute_command_output_all("cp -r " + library_path + " " + install_path)


# def install_app_delay(app_name, customer_name, app_version):
#     myLogger.info_logger("-------RQ install start --------")
#     job_id = app_name + "_" + customer_name

#     try:
#         # 因为这个时候还没有复制文件夹，是从/data/library里面文件读取json来检查的，应该是app_name,而不是customer_name
#         resource_flag = docker.check_vm_resource(app_name)

#         if resource_flag == True:

#             myLogger.info_logger("job check ok, continue to install app")
#             env_path = "/data/apps/" + customer_name + "/.env"
#             # prepare_app(app_name, customer_name)
#             docker.check_app_compose(app_name, customer_name)
#             myLogger.info_logger("start JobID=" + job_id)
#             docker.modify_env(env_path, 'APP_NAME', customer_name)
#             docker.modify_env(env_path, "APP_VERSION", app_version)
#             docker.check_app_url(customer_name)
#             cmd = "cd /data/apps/" + customer_name + " && sudo docker compose pull && sudo docker compose up -d"
#             output = shell_execute.execute_command_output_all(cmd)
#             myLogger.info_logger("-------Install result--------")
#             myLogger.info_logger(output["code"])
#             myLogger.info_logger(output["result"])
#             try:
#                 shell_execute.execute_command_output_all("bash /data/apps/" + customer_name + "/src/after_up.sh")
#             except Exception as e:
#                 myLogger.info_logger(str(e))
#         else:
#             error_info = "##websoft9##" + const.ERROR_SERVER_RESOURCE + "##websoft9##" + "Insufficient system resources (cpu, memory, disk space)" + "##websoft9##" + "Insufficient system resources (cpu, memory, disk space)"
#             myLogger.info_logger(error_info)
#             raise Exception(error_info)
#     except CommandException as ce:
#         myLogger.info_logger(customer_name + " install failed(docker)!")
#         delete_app(job_id)
#         error_info = "##websoft9##" + ce.code + "##websoft9##" + ce.message + "##websoft9##" + ce.detail
#         myLogger.info_logger(error_info)
#         raise Exception(error_info)
#     except Exception as e:
#         myLogger.info_logger(customer_name + " install failed(system)!")
#         delete_app(job_id)
#         error_info = "##websoft9##" + const.ERROR_SERVER_SYSTEM + "##websoft9##" + 'system original error' + "##websoft9##" + str(
#             e)
#         myLogger.info_logger(error_info)
#         raise Exception(error_info)

# def get_createtime(official_app, app_path, customer_name):
#     data_time = ""
#     try:
#         if official_app:
#             cmd = "docker ps -f name=" + customer_name + " --format {{.RunningFor}}  | head -n 1"
#             result = shell_execute.execute_command_output_all(cmd)["result"].rstrip('\n')
#             data_time = result
#         else:
#             cmd_all = "cd " + app_path + " && docker compose ps -a --format json"
#             output = shell_execute.execute_command_output_all(cmd_all)
#             container_name = json.loads(output["result"])[0]["Name"]
#             cmd = "docker ps -f name=" + container_name + " --format {{.RunningFor}}  | head -n 1"
#             result = shell_execute.execute_command_output_all(cmd)["result"].rstrip('\n')
#             data_time = result

#     except Exception as e:
#         myLogger.info_logger(str(e))
#     myLogger.info_logger("get_createtime get success" + data_time)
#     return data_time

# def check_if_official_app(var_path):
#     if docker.check_directory(var_path):
#         if docker.read_var(var_path, 'name') != "" and docker.read_var(var_path, 'trademark') != "" and docker.read_var(
#                 var_path, 'requirements') != "":
#             requirements = docker.read_var(var_path, 'requirements')
#             try:
#                 cpu = requirements['cpu']
#                 mem = requirements['memory']
#                 disk = requirements['disk']
#                 return True
#             except KeyError:
#                 return False
#     else:
#         return False

# # 应用是否已经安装
# def check_app_docker(app_id):
#     customer_name = app_id.split('_')[1]
#     app_name = app_id.split('_')[0]
#     flag = False
#     cmd = "docker compose ls -a | grep \'/" + customer_name + "/\'"
#     try:
#         shell_execute.execute_command_output_all(cmd)
#         flag = True
#         myLogger.info_logger("APP in docker")
#     except CommandException as ce:
#         myLogger.info_logger("APP not in docker")

#     return flag


# def check_app_rq(app_id):
#     myLogger.info_logger("check_app_rq")

#     started = StartedJobRegistry(queue=q)
#     failed = FailedJobRegistry(queue=q)
#     run_job_ids = started.get_job_ids()
#     failed_job_ids = failed.get_job_ids()
#     queue_job_ids = q.job_ids
#     myLogger.info_logger(queue_job_ids)
#     myLogger.info_logger(run_job_ids)
#     myLogger.info_logger(failed_job_ids)
#     if queue_job_ids and app_id in queue_job_ids:
#         myLogger.info_logger("App in RQ")
#         return True
#     if failed_job_ids and app_id in failed_job_ids:
#         myLogger.info_logger("App in RQ")
#         return True
#     if run_job_ids and app_id in run_job_ids:
#         myLogger.info_logger("App in RQ")
#         return True
#     myLogger.info_logger("App not in RQ")
#     return False


#     def get_apps_from_queue():
#     myLogger.info_logger("get queque apps...")
#     # 获取 StartedJobRegistry 实例
#     started = StartedJobRegistry(queue=q)
#     finish = FinishedJobRegistry(queue=q)
#     deferred = DeferredJobRegistry(queue=q)
#     failed = FailedJobRegistry(queue=q)
#     scheduled = ScheduledJobRegistry(queue=q)
#     cancel = CanceledJobRegistry(queue=q)

#     # 获取正在执行的作业 ID 列表
#     run_job_ids = started.get_job_ids()
#     finish_job_ids = finish.get_job_ids()
#     wait_job_ids = deferred.get_job_ids()
#     failed_jobs = failed.get_job_ids()
#     scheduled_jobs = scheduled.get_job_ids()
#     cancel_jobs = cancel.get_job_ids()

#     myLogger.info_logger(q.jobs)
#     myLogger.info_logger(run_job_ids)
#     myLogger.info_logger(failed_jobs)
#     myLogger.info_logger(cancel_jobs)
#     myLogger.info_logger(wait_job_ids)
#     myLogger.info_logger(finish_job_ids)
#     myLogger.info_logger(scheduled_jobs)

#     installing_list = []
#     for job_id in run_job_ids:
#         app = get_rq_app(job_id, 'installing', "", "", "")
#         installing_list.append(app)
#     for job in q.jobs:
#         app = get_rq_app(job.id, 'installing', "", "", "")
#         installing_list.append(app)
#     for job_id in failed_jobs:
#         job = q.fetch_job(job_id)
#         exc_info = job.exc_info
#         code = exc_info.split('##websoft9##')[1]
#         message = exc_info.split('##websoft9##')[2]
#         detail = exc_info.split('##websoft9##')[3]
#         app = get_rq_app(job_id, 'failed', code, message, detail)
#         installing_list.append(app)

#     return installing_list

# #从rq获取app信息
# def get_rq_app(id, status, code, message, detail):
#     app_name = id.split('_')[0]
#     customer_name = id.split('_')[1]
#     # 当app还在RQ时，可能文件夹还没创建，无法获取trade_mark
#     trade_mark = ""
#     app_version = ""
#     create_time = ""
#     volume_data = ""
#     config_path = ""
#     image_url = get_Image_url(app_name)
#     config = None
#     if status == "installing":
#         status_reason = None
#     else:
#         status_reason = StatusReason(Code=code, Message=message, Detail=detail)

#     app = App(app_id=id, app_name=app_name, customer_name=customer_name, trade_mark=trade_mark,
#               app_version=app_version, create_time=create_time, volume_data=volume_data, config_path=config_path,
#               status=status, status_reason=status_reason, official_app=True, image_url=image_url,
#               app_https=False, app_replace_url=False, config=config)
#     return app.dict()


# def get_admin_url(customer_name, url):
#     admin_url = ""
#     path = "/data/apps/" + customer_name + "/.env"
#     try:
#         admin_path = list(docker.read_env(path, "APP_ADMIN_PATH").values())[0]
#         admin_path = admin_path.replace("\"", "")
#         admin_url = url + admin_path
#     except IndexError:
#         pass
#     return admin_url

# def get_container_port(container_name):
#     port = "80"
#     cmd = "docker port " + container_name + " |grep ::"
#     result = shell_execute.execute_command_output_all(cmd)["result"]
#     myLogger.info_logger(result)
#     port = result.split('/')[0]
#     myLogger.info_logger(port)

#     return port