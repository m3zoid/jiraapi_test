"""Here is a class for execution strategies
"""

import time
import string
import random
import requests
import traceback
from jira import JIRA
import makelog
import namebase


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
        names_base = namebase.Namebase()
        maxlen_projname = 10
        content_count = {
                            'project': 10,
                            'user': 10,
                            'component': 20,
                            'issue': 100
                        }

        # making projects
        for i in xrange(content_count['project']):
            newname = names_base.getname_project()
            parts = newname.split()[::2]
            newkey = string.join((parts[0][:(maxlen_projname - len(parts[1]))], parts[1]), '')
            try:
                self._jira_connection.create_project(newkey, name=newname)
                outstr = "Project {} was successfully created".format(newkey)
                self._makelog.putto_console(outstr)
                self._makelog.putto_file(outstr)
            except:
                outstr = "Some problem with project {} creation".format(newkey)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        # making users
        for i in xrange(content_count['user']):
            newname = names_base.getname_user()
            try:
                self._jira_connection.add_user(newname, "{}@mail.net".format(newname),\
                                                fullname="Name {}{}".format(string.upper(newname[:1]), newname[1:]))
                outstr = "User {} was successfully created".format(newname)
                self._makelog.putto_console(outstr)
                self._makelog.putto_file(outstr)
            except:
                outstr = "Some problem with user {} creation".format(newname)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        # getting all valid project keys
        projects_keys = []
        projects_all = self._jira_connection.projects()
        for project in projects_all:
            projects_keys.append(project.key)

        # getting all valid user names
        users_keys = []
        users_all = self._jira_connection.search_users('%', maxResults=False, includeInactive=True)
        for user in users_all:
            users_keys.append(user.name)

        # making components
        for i in xrange(content_count['component']):
            newname = names_base.getname_component()
            try:
                self._jira_connection.create_component(newname, random.choice(projects_keys), leadUserName=random.choice(users_keys))
                outstr = "Component {} was successfully created".format(newname)
                self._makelog.putto_console(outstr)
                self._makelog.putto_file(outstr)
            except:
                outstr = "Some problem with component {} creation".format(newname)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        # making issues
        for i in xrange(content_count['issue']):
            newname = names_base.getname_issue()
            fields = {
                        "project": {
                                        "key": random.choice(projects_keys)
                                    },
                        "summary": "Here should be some random text summary for issue {}".format(newname),
                        "description": "Here should be some random text description for issue {}".format(newname),
                        "issuetype": {
                                        "name": random.choice(("Bug", "Improvement", "Task", "Epic", "New Feature"))
                                    },
                        "assignee": {
                                        "name": random.choice(users_keys)
                                    },
                        "timetracking": {
                                            "originalEstimate": "{}w {}d {}h".format(random.randint(1, 3), random.randint(1, 4), random.randint(1, 7)),
                                            "remainingEstimate": "{}d {}h".format(random.randint(1, 4), random.randint(1, 7))
                                        }
                    }
            try:
                self._jira_connection.create_issue(fields=fields)
                outstr = "Issue {} was successfully created".format(newname)
                self._makelog.putto_console(outstr)
                self._makelog.putto_file(outstr)
            except:
                outstr = "Some problem with issue {} creation".format(newname)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())

        # making worklogs
        issues_all = self._jira_connection.search_issues('', maxResults=False)
        for iss in issues_all:
            try:
                self._jira_connection.add_worklog(iss, timeSpent="{}h".format(random.randint(1, 3)), user=random.choice(users_keys),\
                                                    comment="Here should be some random text about work on this issue")
                outstr = "Worklog for issue {} was successfully created".format(iss.key)
                self._makelog.putto_console(outstr)
                self._makelog.putto_file(outstr)
            except:
                outstr = "Some problem with worklog creation for issue {}".format(iss.key)
                self._makelog.putto_console(outstr)
                self._makelog.putto_errorlog(outstr, traceback.format_exc())
