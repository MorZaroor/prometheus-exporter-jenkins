# prometheus-exporter-jenkins




## Quick-start
- docker run -p 9118:9118 -e PROMETHEUS_EXPORTER_JENKINS_PROTOCOL="__jenkins_protocol_placeholder__" -e PROMETHEUS_EXPORTER_JENKINS_URL="__jenkins_url_placeholder__" -e PROMETHEUS_EXPORTER_JENKINS_USER="__jenkins_user_placeholder__" -e PROMETHEUS_EXPORTER_JENKINS_PASS="__jenkins_pass_placeholder__" __docker_repo_placeholder__.jfrog.io/prometheus-exporter-jenkins:${version}