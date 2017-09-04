"""Here is a class for execution strategies
"""

import time
import requests
import traceback
from jira import JIRA
import makelog


class Strategy:
    def __init__(self, account_name, user_name, user_password):
        self._account = account_name
        self._user = user_name
        self._password = user_password
        self._server = 'https://{}.atlassian.net'.format(self._account)
        self._jira_connection = JIRA(server=self._server, basic_auth=(self._user, self._password))
        self._makelog = makelog.Makelog('output', 'errorlog')

    def execute(self, key):
        if key == 1:
            self._doreporting()
        elif key == 2:
            self._domailing()
        elif key == 3:
            self._dogenerating()
        elif key == 4:
            self._dotesting()
        else:
            return False

    def _doreporting(self):
        data_peruser = {}
        data_percomponent = {}

        # getting all users
        users_all = self._jira_connection.search_users('%', maxResults=False, includeInactive=True)
        for user in users_all:
            data_peruser[user.name] = {
                                        'time_total': 0,
                                        'time_perissue': {},
                                        'actual_name': user.displayName,
                                        'components': set()
                                        }

        # getting all components
        components_all = set()
        projects_all = self._jira_connection.projects()
        for project in projects_all:
            try:
                comps = self._jira_connection.project_components(project)
                components_all.update(comps)
            except:
                outstr = "Unexpected error with getting components from project: {}".format(project.key)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        for comp in components_all:
            try:
                component_data = self._jira_connection.component(comp.id)
                data_percomponent[component_data.id] = {
                                                        'name': component_data.name,
                                                        'projectkey': component_data.project,
                                                        'time_total': 0,
                                                        'time_perissue': {},
                                                        'lead': '' if not hasattr(component_data, 'lead') else component_data.lead.name
                                                        }
                if hasattr(component_data, 'lead'):
                    data_peruser[component_data.lead.name]['components'].add(component_data.id)
            except:
                outstr = "Unexpected error with getting data of component id: {}".format(comp.id)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        # counting hours logic
        issues_all = self._jira_connection.search_issues('', maxResults=False)
        for iss in issues_all:
            try:
                iss_works = self._jira_connection.worklogs(iss)
                for work in iss_works:
                    # per user
                    data_peruser[work.author.name]['time_total'] += work.timeSpentSeconds
                    if iss.key not in data_peruser[work.author.name]['time_perissue']:
                        data_peruser[work.author.name]['time_perissue'][iss.key] = 0
                    data_peruser[work.author.name]['time_perissue'][iss.key] += work.timeSpentSeconds

                    # per valid component (with lead)
                    for comp in iss.fields.components:
                        if data_percomponent[comp.id]['lead'] == work.author.name:
                            data_percomponent[comp.id]['time_total'] += work.timeSpentSeconds
                            if iss.key not in data_percomponent[comp.id]['time_perissue']:
                                data_percomponent[comp.id]['time_perissue'][iss.key] = 0
                            data_percomponent[comp.id]['time_perissue'][iss.key] += work.timeSpentSeconds
            except:
                outstr = "Unexpected error counting hours with issue: {}".format(iss.key)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        # outputting data
        outstr = ""
        outstr += "\t\t\tReport on the spent hours:\n"
        outstr += "\n\t\tPer programmer:\n\n"
        for user_name, user_dat in data_peruser.iteritems():
            outstr += "-> Name: {} ({})\n".format(user_dat['actual_name'], user_name)
            outstr += "   Total time: {} hour(s)\n".format(str(user_dat['time_total'] / 3600))
            outstr += "   Time per issue:\n"
            for iss_key, time_val in user_dat['time_perissue'].iteritems():
                outstr += "\t{} is: {} hour(s)\n".format(iss_key, str(time_val / 3600))

            outstr += "\n"

        outstr += "\n\t\tPer component (with lead only):\n\n"
        for comp_id, comp_dat in data_percomponent.iteritems():
            outstr += "-> Name: {} ({})\n".format(comp_dat['name'], comp_dat['projectkey'])
            outstr += "   Lead: {}\n".format(comp_dat['lead'])
            outstr += "   Total time: {} hour(s)\n".format(str(comp_dat['time_total'] / 3600))
            outstr += "   Time per issue:\n"
            for iss_key, time_val in comp_dat['time_perissue'].iteritems():
                outstr += "\t{} is: {} hour(s)\n".format(iss_key, str(time_val / 3600))

            outstr += "\n"

        outstr += "\n-----> END REPORT <-----\n\n"
        self._makelog.putto_console(outstr, iscln=True)
        self._makelog.putto_file(outstr)

    def _domailing(self):
        issues_tonotify = []
        issues_all = self._jira_connection.search_issues('', maxResults=False)
        for iss in issues_all:
            try:
                iss_data = self._jira_connection.issue(iss)
                if (iss_data.fields.timeestimate is None) or (len(iss_data.fields.components) == 0):
                    issues_tonotify.append({
                                                'name':     iss_data.fields.assignee.name,
                                                'dispname': iss_data.fields.assignee.displayName,
                                                'email':    iss_data.fields.assignee.emailAddress,
                                                'isskey':   iss.key
                                            })
            except:
                outstr = "Unexpected error with getting issue: {}".format(iss.key)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        for data in issues_tonotify:
            try:
                url = "{}/rest/api/2/issue/{}/notify".format(self._server, data['isskey'])
                notify_data = {
                                "subject": "You have some incomplete fields in issue {}".format(data['isskey']),
                                "textBody": "Your got this notification because have one or couple incomplete fields in {} issue. Note, that 'estimates' \
                                            and 'component' fields are mandatory. Please, check this fields and fill its in if need.".format(data['isskey']),
                                "to": {"users": [{"name": data['name']}]},
                            }

                requests.post(url, auth=(self._user, self._password), json=notify_data)
                outstr = "Successfully sending notification to:\n-> {} {} about incomplete fields in {} issue".format(data['dispname'], data['email'], data['isskey'])
                self._makelog.putto_console(outstr)
                self._makelog.putto_file(outstr)
            except:
                outstr = "Unexpected error with sending notification to:\n-> {} {} about: {}".format(data['dispname'], data['email'], data['isskey'])
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        if len(issues_tonotify) == 0:
            self._makelog.putto_console("All tested issues were filed in correct")

    def _dogenerating(self):
        pass

    def _dotesting(self):
        pass

        # new_issue = authed_jira.create_issue(project='PROJKEY1', summary='New issue from jira-python',
        #                                     description='Look into this one', issuetype={'name': 'Bug'})
        # print new_issue.fields.summary
        # print authed_jira.projects()

        # issue = authed_jira.issue('PROJKEY1-1')
        # print issue.fields.summary
        # print issue.fields.description

        # add_user(username, email, directoryId=1, password=None, fullname=None, notify=False, active=True, ignore_existing=False)
        # create_project(key, name=None, assignee=None, type='Software', template_name=None)
        # create_component(name, project, description=None, leadUserName=None, assigneeType=None, isAssigneeTypeValid=False)
        # create_issue(fields=None, prefetch=True, **fieldargs)
        # add_worklog(issue, timeSpent=None, timeSpentSeconds=None, adjustEstimate=None, newEstimate=None, reduceBy=None, comment=None, started=None, user=None)
