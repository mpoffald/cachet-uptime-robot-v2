#!/usr/bin/env python3
import json
import sys
import time
import configparser
from urllib import request
from urllib import parse ##updating to requests library
import requests
from datetime import datetime


class UptimeRobot(object):
    """ Intermediate class for setting uptime stats.
    """
    def __init__(self, api_key, authuser, authpass):
        self.api_key = api_key
        self.base_url = 'https://api.uptimerobot.com/v2/getMonitors'
        self.authuser = authuser
        self.authpass = authpass
    def get_monitors(self, response_times=1, logs=1, uptime_ratio=30):
        """
        Returns status and response payload for all known monitors.
        """
        print('GET MONITORS')
        endpoint = self.base_url
        data = {
                'api_key': format(self.api_key),
                'format': 'json',
                # responseTimes - optional (defines if the response time data of each
                # monitor will be returned. Should be set to 1 for getting them.
                # Default is 0)
                'response_times': format(response_times),
                 # logs - optional (defines if the logs of each monitor will be
                # returned. Should be set to 1 for getting the logs. Default is 0)
                'logs': format(logs),
                # customUptimeRatio - optional (defines the number of days to calculate
                # the uptime ratio(s) for. Ex: customUptimeRatio=7-30-45 to get the
                # uptime ratios for those periods)
                'custom_uptime_ratios': format(uptime_ratio)
            } ##NOTE used to be encoding here 


        
        headers={'content-type': "application/x-www-form-urlencoded",'cache-control': "no-cache"}

        # Verifying in the response is jsonp in otherwise is error

        response = requests.request('POST', endpoint, data=data, headers=headers, auth=(authuser, authpass))

    

        ##get rsponse and convert to json
        j_content = response.json()

        if j_content.get('stat'):
            stat = j_content.get('stat')
            if stat == 'ok':

                return True, j_content

        return False, j_content


class CachetHq(object):
    # Uptime Robot status list
    UPTIME_ROBOT_PAUSED = 0
    UPTIME_ROBOT_NOT_CHECKED_YET = 1
    UPTIME_ROBOT_UP = 2
    UPTIME_ROBOT_SEEMS_DOWN = 8
    UPTIME_ROBOT_DOWN = 9

    # Cachet status list
    CACHET_OPERATIONAL = 1
    CACHET_PERFORMANCE_ISSUES = 2
    CACHET_SEEMS_DOWN = 3
    CACHET_DOWN = 4

    def __init__(self, cachet_api_key, cachet_url, authuser, authpass):
        self.cachet_api_key = cachet_api_key
        self.cachet_url = cachet_url
        self.authuser = authuser
        self.authpass = authpass #request does not have "auth", try switching to requests (import requests and maybe update query syntax)


    def update_component(self, id_component=1, status=None):
        component_status = None

        # Not Checked yet and Up
        if status in [self.UPTIME_ROBOT_NOT_CHECKED_YET, self.UPTIME_ROBOT_UP]:
            component_status = self.CACHET_OPERATIONAL

        # Seems down
        elif status == self.UPTIME_ROBOT_SEEMS_DOWN:
            component_status = self.CACHET_SEEMS_DOWN

        # Down
        elif status == self.UPTIME_ROBOT_DOWN:
            component_status = self.CACHET_DOWN
        print('UPDATE COMPONENT')
        if component_status:
            url = '{0}/api/v1/{1}/{2}'.format(
                self.cachet_url,
                'components',
                id_component
            )

            data = {
                'status': component_status,
            }

            headers={'X-Cachet-Token': self.cachet_api_key}
            '''
            req = request.Request(
                url=url,
                data=data,
                method='PUT',
                headers={'X-Cachet-Token': self.cachet_api_key},

            )
            '''
            response = requests.request('PUT', url, data=data, headers=headers, auth=(self.authuser, self.authpass))
            print('REQUEST MADE')
#            response = request.urlopen(req)
#            content = response.read().decode('utf-8')
            print('update compnent complete')
 #           return content
            return response

    def set_data_metrics(self, value, timestamp, id_metric=1):
        print('SET DATA METRICS')
        url = '{0}/api/v1/metrics/{1}/points'.format(
            self.cachet_url,
            id_metric
        )

        print("metric url (should be 2): " + str(url))
#        data = OAparse.urlencode({
        data = {
            'value': value,
            'timestamp': timestamp,
        }
        '''
        req = request.Request(
            url=url,
            data=data,
            method='POST',
            headers={'X-Cachet-Token': self.cachet_api_key},
        )
        '''
        headers={'X-Cachet-Token': self.cachet_api_key}
        
        response = requests.request('POST', url, data=data, headers=headers, auth=(self.authuser, self.authpass))
        
        print('response in set_data_metrics: ' + str(response))
 #       return json.loads(response.read().decode('utf-8'))
        return response.json()

    def get_last_metric_point(self, id_metric):
        print('GET LAST METRIC POINT')
        url = '{0}/api/v1/metrics/{1}/points'.format(
            self.cachet_url,
            id_metric
        )

        req = request.Request(
            url=url,
            method='GET',
            headers={'X-Cachet-Token': self.cachet_api_key},
        )

        req.auth = self.auth
        response = request.urlopen(req)
        content = response.read().decode('utf-8')

        last_page = json.loads(
            content
        ).get('meta').get('pagination').get('total_pages')

        url = '{0}/api/v1/metrics/{1}/points?page={2}'.format(
            self.cachet_url,
            id_metric,
            last_page
        )

        req = request.Request(
            url=url,
            method='GET',
            headers={'X-Cachet-Token': self.cachet_api_key},
        )

        req.auth=self.auth
        response = request.urlopen(req)
        content = response.read().decode('utf-8')

        if json.loads(content).get('data'):
            data = json.loads(content).get('data')[0]
        else:
            data = {
                'created_at': datetime.now().date().strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
            }

        return data


class Monitor(object):
    def __init__(self, monitor_list, api_key, authuser, authpass):
        self.monitor_list = monitor_list
        self.api_key = api_key
        self.authuser = authuser
        self.authpass = authpass

    def send_data_to_catchet(self, monitor):
        """ Posts data to Cachet API.
            Data sent is the value of last `Uptime`.
        """
        try:
            website_config = self.monitor_list[monitor.get('url')]
        except KeyError:
            print('ERROR: monitor is not valid')
            sys.exit(1)

        cachet = CachetHq(
            cachet_api_key=website_config['cachet_api_key'],
            cachet_url=website_config['cachet_url'],
            authuser=self.authuser,
            authpass=self.authpass,
        )

        if 'component_id' in website_config:
            cachet.update_component(
                website_config['component_id'],
                int(monitor.get('status'))
            )

        metric = cachet.set_data_metrics(
            monitor.get('custom_uptime_ratio'),
            int(time.time()),
            website_config['metric_id']
        )
        print('Metric created: {0}'.format(metric))

    def update(self):
        """ Update all monitors uptime and status.
        """
        uptime_robot = UptimeRobot(self.api_key, self.authuser, self.authpass)
        success, response = uptime_robot.get_monitors(response_times=1)
        if success:
            monitors = response.get('monitors')
            for monitor in monitors:
                if monitor['url'] in self.monitor_list:
                    print('Updating monitor {0}. URL: {1}. ID: {2}'.format(
                        monitor['friendly_name'],
                        monitor['url'],
                        monitor['id'],
                    ))
                    self.send_data_to_catchet(monitor)
        else:
            print('ERROR: No data was returned from UptimeMonitor')


if __name__ == "__main__":
    CONFIG = configparser.ConfigParser()
    CONFIG.read(sys.argv[1])
    SECTIONS = CONFIG.sections()

    if not SECTIONS:
        print('ERROR: File path is not valid')
        sys.exit(1)

    UPTIME_ROBOT_API_KEY = None
    MONITOR_DICT = {}
    for section in SECTIONS:
        if section == 'uptimeRobot':
            uptime_robot_api_key = CONFIG[section]['UptimeRobotMainApiKey']
        elif section == 'cachet_auth':
            authuser = CONFIG[section]['Authuser']
            authpass = CONFIG[section]['Authpass']
        else:
            MONITOR_DICT[section] = {
                'cachet_api_key': CONFIG[section]['CachetApiKey'],
                'cachet_url': CONFIG[section]['CachetUrl'],
                'metric_id': CONFIG[section]['MetricId'],
            }
            if 'ComponentId' in CONFIG[section]:
                MONITOR_DICT[section].update({
                    'component_id': CONFIG[section]['ComponentId'],
#                    'authuser':CONFIG[element]['Authuser'],
#                    'authpass':CONFIG[element]['Authpass'],
                })
        

    MONITOR = Monitor(monitor_list=MONITOR_DICT, api_key=uptime_robot_api_key, authuser=authuser, authpass=authpass)
    MONITOR.update()
