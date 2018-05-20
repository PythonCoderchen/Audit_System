import time
import multiprocessing
import sys,os,json
import paramiko



def cmd_run(tasklog_id,task_id,cmd_str):
    try:
        import django
        django.setup()
        from audit import models
        tasklog_obj = models.TaskLog.objects.get(id=tasklog_id)
        print('run cmd:', tasklog_obj, cmd_str)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(tasklog_obj.host_user_bind.host.ip_addr,
                    tasklog_obj.host_user_bind.host.port,
                    tasklog_obj.host_user_bind.host_user.username,
                    tasklog_obj.host_user_bind.host_user.password,
                    timeout=15)
        stdin, stdout, stderr = ssh.exec_command(cmd_str)

        result = stdout.read() + stderr.read()
        result = result.decode('utf-8')
        print('---------%s--------' % tasklog_obj.host_user_bind)
        print(result)
        ssh.close()

        tasklog_obj.result = result or 'cmd has no result output .'
        tasklog_obj.status = 0
        tasklog_obj.save()

    except Exception as e:
        print("error :", e)


def file_transfer(tasklog_id,task_id,task_content):
        import django
        django.setup()
        from audit import models
        from django.conf import settings

        tasklog_obj = models.TaskLog.objects.get(id=tasklog_id)
        try:
            print('task content:', tasklog_obj)
            task_data = json.loads(tasklog_obj.task.content)


            t = paramiko.Transport(tasklog_obj.host_user_bind.host.ip_addr,tasklog_obj.host_user_bind.host.port)
            t.connect(username=tasklog_obj.host_user_bind.host_user.username,password=tasklog_obj.host_user_bind.host_user.password)
            sftp = paramiko.SFTPClient.from_transport(t)
            if task_data.get('file_transfer_type') == 'send':
                local_path = "%s/%s/%s"%(settings.FILE_UPLOADS,
                                         tasklog_obj.task.account.id,
                                         task_data.get('random_str'))
                print(local_path)
                for file_name in os.listdir(local_path):
                    sftp.put('%s/%s' %(local_path,file_name),'%s/%s'%(task_data.get('remote_path'),file_name))
            else:
                download_dir = "{download_base_dir}/{task_id}".format(download_base_dir=settings.FILE_DOWNLOADS,task_id=task_id)
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir,exist_ok=True)
                remote_filename = os.path.basename(task_data.get('remote_path'))
                local_path = "%s/%s.%s"%(download_dir,tasklog_obj.host_user_bind.host.ip_addr,remote_filename)
                sftp.get(task_data.get('remote_path'),local_path)
                tasklog_obj.result = 'get remote file [%s] to local done'% task_data.get('remote_path')

            t.close()
            tasklog_obj.status = 0
            tasklog_obj.save()
            # ssh = paramiko.SSHClient()
            # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        except Exception as e:
            print(e)
            tasklog_obj.result = str(e)
            tasklog_obj.save()

if __name__ == '__main__':

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) )
    sys.path.insert(0,BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Audit_System.settings")
    import django
    django.setup()


    from audit import models


    task_id = sys.argv[1]
    #1、根据Taskid拿到任务对象
    #2、拿到任务类型关联的所有主机
    #3、根据任务类型调用多进程，执行不同的方法
    #4、每个子任务执行完后 自己把结果写入数据库

    task_obj = models.Task.objects.get(id = task_id)
    pool = multiprocessing.Pool(processes=10)
    if task_obj.task_type == 0:
        task_func = cmd_run
    else:
        task_func = file_transfer

    for tasklog_obj in task_obj.tasklog_set.all():
        pool.apply_async(task_func,args=(tasklog_obj.id,task_obj.id,task_obj.content))

    pool.close()
    pool.join()


















