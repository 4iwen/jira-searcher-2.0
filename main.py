from datetime import datetime
from flask import Flask, render_template, request
from jira import JIRA
import configparser

ISSUE_TYPES = ["Bug",
               "Certification task",
               "DOC bug",
               "DOC task",
               "HW-task",
               "Research",
               "Research Task",
               "Story",
               "Task"]
STATUS_TYPES = ["Approved",
                "Cancelled",
                "Confirmed",
                "DONE",
                "Done",
                "Done Unreleased",
                "Done-unreleased",
                "Implemented",
                "Parked",
                "Pending Peer Review",
                "Processed",
                "Rejected",
                "Released",
                "SOLVED"]
ORDER_TYPES = ["BC1000518 r R&D overhead",
               "BC1001164 v New router functions",
               "BC1001172 v New functions for RSeeNet",
               "BC1001186 r Routers support",
               "BC1001187 r RSeeNet support",
               "BC1001201 r Maintenance of manuf.machines",
               "BC1001228 v OWL LTE M12",
               "BC1001236 v CP30 a CP30+ pro Radium",
               "BC1001237 r Other support",
               "BC1001238 r VPN portal",
               "BC1001239 r Engineering portal",
               "BC1001240 r Testlab",
               "BC1001241 v OWL LTE M12 PoE",
               "BC1001242 v OWL LTE M12 IPv6",
               "BC1001244 r SWH support",
               "BC1001245 v SmartStart SL31",
               "BC1001248 v ICR-3211 LTE cat.M",
               "BC1001249 v RWPB box replacement",
               "BC1001250 v Router v4",
               "BC1001251 v Router ICR-3831",
               "BC1001252 v ICR OEM Hirschmann",
               "BC1001253 v ICR-3201",
               "BC1001254 v UR5i v2 Libratum (Egypt)",
               "BC1001255 v ICR-2331-T",
               "BC1001256 v SmartFlex 2x RS485",
               "BC1001257 v CR10 v2 - CE Renewal",
               "BC1001258 v ICR-2031",
               "BC1001259 v SmartStart SL305",
               "BC1001260 v ICR-2631 [ICR-2734 now]",
               "BC1001261 r WebAccess/DMP",
               "BC1001262 v ICR-2531-TPOL",
               "BC1001263 v Low Cost 5G Router",
               "BC1001264 v New OS for Routers",
               "BC1001265 v WebAccess/DMP GEN3",
               "BC1001266 NRE",
               "BC1001267 NRE Extra cost",
               "BC1001268 v WebAccess/DMP GEN2 New Features",
               "BC1001269 NRE Bausch & Lomb",
               "BC1001270 v Platform v2i"]

config_parser = configparser.ConfigParser()
config_parser.read('config.ini')
cfg = config_parser['DEFAULT']

jira = JIRA(cfg['url'], basic_auth=(cfg['email'], cfg['jira_api_token']))
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


def get_work_log_data(min_date,
                      max_date,
                      selected_issue_types,
                      selected_status_types,
                      selected_order_types):
    data = []
    jql_cmd = ""

    if len(selected_issue_types) != 0:
        jql_cmd += f'issueType IN ("'
        jql_cmd += str("\", \"".join(selected_issue_types))
        jql_cmd += '") AND '

    if len(selected_status_types) != 0:
        jql_cmd += 'status IN ("'
        jql_cmd += str("\", \"".join(selected_status_types))
        jql_cmd += '") AND '

    if len(selected_order_types) != 0:
        jql_cmd += '"Order[Dropdown]" IN ("'
        jql_cmd += str("\", \"".join(selected_order_types))
        jql_cmd += '") AND '

    jql_cmd += str(f'worklogDate >= "{min_date.replace("-", "/")}" AND '
                   f'worklogDate <= "{max_date.replace("-", "/")}"')

    issues = jira.search_issues(jql_cmd,
                                maxResults=0,
                                fields=['worklog', 'project', 'Order'])

    for issue in issues:
        work_logs2 = issue.raw["fields"]["worklog"]["worklogs"]
        for work_log in work_logs2:
            creation_date = work_log["started"]
            if min_date <= creation_date <= max_date:
                date_obj = datetime.strptime(work_log["started"], "%Y-%m-%dT%H:%M:%S.%f%z")
                data.append([issue.raw["fields"]["project"]["key"],
                             issue.raw["key"],
                             issue.fields.customfield_12400,
                             work_log["author"]["displayName"],
                             float(work_log["timeSpentSeconds"] / 3600),
                             date_obj.strftime("%d-%m-%Y %H:%M:%S")])

    return data


def get_work_time_data(min_date,
                      max_date):
    data = []
    jql_cmd = ""
    jql_cmd += f'issueType IN ("'
    jql_cmd += str("\", \"".join(ISSUE_TYPES))
    jql_cmd += '") AND '
    jql_cmd += 'status IN ("'
    jql_cmd += str("\", \"".join(STATUS_TYPES))
    jql_cmd += '") AND '
    jql_cmd += '"Order[Dropdown]" IN ("'
    jql_cmd += str("\", \"".join(ORDER_TYPES))
    jql_cmd += '") AND '

    jql_cmd += str(f'worklogDate >= "{min_date.replace("-", "/")}" AND '
                   f'worklogDate <= "{max_date.replace("-", "/")}"')

    issues = jira.search_issues(jql_cmd,
                                maxResults=0,
                                fields=['worklog'])

    for issue in issues:
        work_logs2 = issue.raw["fields"]["worklog"]["worklogs"]
        for work_log in work_logs2:
            creation_date = work_log["started"]
            if min_date <= creation_date <= max_date:
                data.append([work_log["author"]["displayName"],
                             float(work_log["timeSpentSeconds"]) / 3600])

    new_array = []
    if len(data) > 0:
        data.sort(key=lambda x: x[0])
        i = 1
        lastname = data[0][0]
        sum_var = data[0][1]
        while i < len(data):
            if lastname != data[i][0]:
                new_array.append([lastname, sum_var])
                sum_var = 0
            lastname = data[i][0]
            sum_var += data[i][1]
            i += 1
        new_array.append([lastname, sum_var])

    return new_array


@app.route('/work-logs')
def work_logs():
    return render_template('work-logs.html',
                           headings=('Project',
                                     'Issue',
                                     'Order',
                                     'Name',
                                     'Time Spent (h)',
                                     'Date'),
                           data=(()),
                           issue_types=ISSUE_TYPES,
                           status_types=STATUS_TYPES,
                           order_types=ORDER_TYPES)


@app.route('/work-logs', methods=['POST'])
def work_logs_search():
    data = get_work_log_data(request.form['min-date-input'],
                             request.form['max-date-input'],
                             request.form.getlist(f'issue-type-input'),
                             request.form.getlist(f'status-type-input'),
                             request.form.getlist(f'order-type-input'))

    return render_template('work-logs.html',
                           headings=('Project',
                                     'Issue',
                                     'Order',
                                     'Name',
                                     'Time Spent (h)',
                                     'Date'),
                           data=data,
                           issue_types=ISSUE_TYPES,
                           status_types=STATUS_TYPES,
                           order_types=ORDER_TYPES), 200


@app.route('/work-time')
def work_time():
    return render_template('work-time.html',
                           headings=('Name',
                                     'Time Spent (h)'),
                           data=(()))


@app.route('/work-time', methods=['POST'])
def work_time_search():
    data = get_work_time_data(request.form['min-date-input'],
                              request.form['max-date-input'])

    return render_template('work-time.html',
                           headings=('Name',
                                     'Time Spent (h)'),
                           data=data), 200


if __name__ == '__main__':
    app.run(host=cfg['host'], port=int(cfg['port']))
