grafana_ini = """

[security]

admin_user = admin
admin_password = $PASS 
    
"""
grafana_provisioning = """
apiVersion: 1

datasources:
  - name: prometheus
    type: prometheus
    access: proxy
    orgId: 1
    url: http://localhost:9090
    isDefault: true
    version: 1
    editable: true       
"""

dashboard_provisioning = """
apiVersion: 1
providers:
 - name: 'default'
   orgId: 1
   folder: ''
   folderUid: ''
   type: file
   options:
     path: /var/lib/grafana/dashboards
"""


prometheus_conf = """
global:
  scrape_interval:     15s
  evaluation_interval: 15s

rule_files:

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']
"""
