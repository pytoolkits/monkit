monkit ping和url监控agent

```python
[root@alqd-01 scripts]# pip install monkit

[root@alqd-01 scripts]# cat monkit.yaml
get_conf_url: http://xxxxx/ops/monitor/agents/get_tasks/
push_mon_url: http://xxxxx/ops/monitor/n9e/push
endpoint: 47.105.38.xx

[root@alqd-01 scripts]# crontab -l
* * * * * /usr/bin/monurl -f /opt/scripts/monkit.yaml

```
