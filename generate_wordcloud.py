from pygerrit2.rest import GerritRestAPI
from requests.auth import HTTPBasicAuth
import json
import os
import git
from subprocess import call
import concurrent.futures

gerrit = GerritRestAPI(url="https://review.lineageos.org")

accounts_dir = 'db/accounts'
projects_dir = 'db/projects'
stats_dir = 'db/stats'
out_dir = 'out'

directories = [accounts_dir, projects_dir, stats_dir, out_dir]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

repeat = True
accounts = []
while repeat:
    accounts.extend(gerrit.get('/accounts/?q=-name:""&n=20&S={}'.format(len(accounts))))
    if '_more_accounts' not in accounts[-1]:
        repeat = False
for account in accounts:
    print('Fetching account {}'.format(account['_account_id']))
    file = open("{}/{}".format(accounts_dir, account['_account_id']), "w")
    file.write(")]}'\n")
    file.write(json.dumps(gerrit.get('/accounts/{}'.format(account['_account_id'])), indent=2))
    file.write('\n')
    file.close()

def repo_fetch(project):
    repodir = os.path.join(projects_dir,project,'.git')
    os.makedirs(repodir)
    project_stats_dir = os.path.join(stats_dir,project)
    os.makedirs(project_stats_dir)
    call(['git', '-C', repodir, 'init'])
    call(['git', '-C', repodir, 'remote', 'add', 'origin', 'https://github.com/'+project])
    call(['git', '-C', repodir, 'fetch', 'origin'])
    call(['git', '-C', repodir, 'fetch', 'origin'])
    f = open(project_stats_dir+'/all_stats.dat', 'w')
    call(['git', '-C', repodir, 'shortlog', '-esn', '--all'], stdout=f)
    f.close()
    f = open(project_stats_dir+'/translations_stats.dat', 'w')
    call(['git', '-C', repodir, 'shortlog', '-esn', '--all', '--grep="Automatic translation import"'], stdout=f)
    f.close()

projects = gerrit.get('/projects/?p=LineageOS')
executor = concurrent.futures.ProcessPoolExecutor(8)
futures = [executor.submit(repo_fetch, project) for project in projects]
concurrent.futures.wait(futures)

call(['java', '-Dfile.encoding=UTF-8', '-classpath', '"./lib/*"', 'CloudGenerator'])

print("====================================")
print("== Cloud generated: {}/cloud.zip ==").format(out_dir)
print("====================================")
