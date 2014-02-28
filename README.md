dftp
====

一个根据关键字来远程下载ftp内容的脚本


```python
host = ''       #主机host
username = ''   #ftp用户名
passwd = ''     #ftp密码
#port = 21      #ftp端口号，默认21
dir_local = ''  #下载到本地的路径
dir_remote = '' #ftp远程路径

dftp = DFTP(host, username, passwd, dir_remote)
dftp.login()    #登录方法

keyword = ''    #需要查找的关键字
fdict = dftp.rndict(dir_remote) #指定ftp远程路径，返回以文件夹名和文件名为keys,路径为values的字典
result = find_keyword(fdict, keyword) #关键字查找的返回结果，为路径和文件名的list
download(dir_local, result, dftp) #下载查找到的结果到指定的本地路径
```

![dftp](http://blog-tdoly-com.u.qiniudn.com/@/github/dftp.png "dftp")
