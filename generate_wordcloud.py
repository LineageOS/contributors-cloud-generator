from pygerrit2.rest import GerritRestAPI
from requests.auth import HTTPBasicAuth
import json
import os, sys
import git
from subprocess import call
import concurrent.futures
import argparse

gerrit = GerritRestAPI(url="https://review.lineageos.org")

accounts_dir = 'db/accounts'
projects_dir = 'db/projects'
stats_dir = 'db/stats'
out_dir = 'out'

parser = argparse.ArgumentParser()
parser.add_argument('--mirror', metavar='mirror_dir', type=str, dest=mirror,
                    help='path to mirror repo')
args = parser.parse_args()

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
    project_stats_dir = os.path.join(stats_dir,project)
    if not os.path.exists(directory):
        os.makedirs(directory)
    repodir = os.path.join(projects_dir,project,'.git')
    if os.path.exists(repodir):
        call(['git', '-C', repodir, 'fetch', 'origin'])
    else:
        os.makedirs(repodir)
        if args.reference:
            call(['git', 'clone', '--no-checkout', '--mirror', os.path.join(args.reference,project+'.git'), 'https://github.com/'+project, repodir])
        else:
            call(['git', 'clone', '--no-checkout', 'https://github.com/'+project, repodir])

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
