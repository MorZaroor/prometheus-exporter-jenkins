import os
import re
import time
import requests
import json
from prometheus_client import start_http_server, Summary
from prometheus_client.core import InfoMetricFamily, REGISTRY

COLLECTION_TIME = Summary('jenkins_collector_collect_seconds', 'Time spent to collect metrics from Jenkins')

class JenkinsCollector(object):
    statuses = ["color", "labelExpression", "queueItem[why]"]
    modded_statuses = [status.replace('[','_').replace(']','') for status in statuses]

    def __init__(self, baseurl, username, password):
        self._baseurl = baseurl
        self._username = username
        self._password = password

    def collect(self):
        start = time.time()

        jobs = self.get_running_jobs_data()

        self._setup_empty_prometheus_metrics()

        for job in jobs:
            name = job['name']
            print("Found Job: {}".format(name))
            print(job)
            self._get_metrics(name, job)

        for status in self.modded_statuses:
            for metric in self._prometheus_metrics[status].values():
                yield metric

        duration = time.time() - start
        COLLECTION_TIME.observe(duration)

    def get_running_jobs_data(self):
        url = '{0}/api/json'.format(self._baseurl)
        tree = 'jobs[name,url,{0}]'.format(','.join([s for s in self.statuses]))
        params = {
            'tree': tree,
        }

        def parse_jobs_data(url):
            result = request_data(url,params)

            jobs = []
            for job in result['jobs']:
                if job['_class'] == 'org.jenkinsci.plugins.workflow.job.WorkflowJob' or \
                   job['_class'] == 'hudson.model.FreeStyleProject':
                    jobs.append(job)
            return jobs

        def request_data(url,params):
            response = requests.get(url, params=params, auth=(self._username, self._password))
            if response.status_code != requests.codes.ok:
                raise Exception("Call to url %s failed with status: %s" % (url, response.status_code))
            result = response.json()
            return result

        return parse_jobs_data(url)

    def _setup_empty_prometheus_metrics(self):
        self._prometheus_metrics = {}
        for status in self.modded_statuses:
            snake_case = re.sub('([A-Z])', '_\\1', status).lower()
            self._prometheus_metrics[status] = {
                'job_status':
                    InfoMetricFamily('jenkins_job_{0}'.format(snake_case),
                                      'Jenkins job {0}'.format(status), labels=["jobname"]),
                
            }
    
    def _get_metrics(self, name, job):
        for status in self.statuses:
            if '[' in status: # queueItem[why]
                status_deep = status.split(']')[0].split('[') # queueItem, why
                modded_status = status.replace('[','_').replace(']','') # queueItem_why
                status = status_deep[0] # queueItem
            if status in job.keys():
                if type(job[status]) == dict:
                    status_data = job[status_deep[0]][status_deep[1]] or {}
                    self._add_data_to_prometheus_structure(status, status_data, job, name, modded_status)
                else:
                    status_data = job[status] or {}
                    self._add_data_to_prometheus_structure(status, status_data, job, name)

    def _add_data_to_prometheus_structure(self, status, status_data, job, name, metric_name=None):
        if status_data.__len__() != 0:
            if type(job[status]) == dict:
                job[status] = json.dumps(job[status])
            if metric_name != None:    
                self._prometheus_metrics[metric_name]['job_status'].add_metric([name], {status: job[status]})
            else:
                self._prometheus_metrics[status]['job_status'].add_metric([name], {status: job[status]})

def main():
    try:
        baseurl = os.environ['PROMETHEUS_EXPORTER_JENKINS_PROTOCOL'] + '://' + os.environ['PROMETHEUS_EXPORTER_JENKINS_URL']
        username = os.environ['PROMETHEUS_EXPORTER_JENKINS_USER']
        password = os.environ['PROMETHEUS_EXPORTER_JENKINS_PASS']
        REGISTRY.register(JenkinsCollector(baseurl, username, password))
        start_http_server(9118)
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)


main()
