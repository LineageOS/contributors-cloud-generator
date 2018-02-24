from pygerrit2.rest import GerritRestAPI
from requests.auth import HTTPBasicAuth
import json
import os, sys
import subprocess
import concurrent.futures
import argparse
import time
import signal

gerrit = GerritRestAPI(url="https://review.lineageos.org")

accounts_dir = 'db/accounts'
projects_dir = 'db/projects'
stats_dir = 'db/stats'
out_dir = 'out'

parser = argparse.ArgumentParser()
parser.add_argument('--mirror', metavar='mirror_dir', type=str, dest='mirror',
                    help='path to mirror repo')
args = parser.parse_args()

os.setpgrp()

def signal_handler(signal_passed, frame):
    print('Killing subprocesses...')
    os.killpg(0, signal.SIGKILL)
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

directories = [accounts_dir, projects_dir, stats_dir, out_dir]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

repeat = True
accounts = []
while repeat:
    r = gerrit.get('/accounts/?q=-username:""&S={}'.format(len(accounts)))
    accounts.extend(r)
    print('\rDownloading accounts list... Total viable accounts found = {}'.format(len(accounts)), end='')
    if '_more_accounts' not in r[-1]:
        repeat = False
print('\nFinished getting accounts list. Total accounts = {}'.format(len(accounts)))
for i,account in enumerate(accounts):
    acc_len = len(accounts)
    print('\rFetching account number {} ({} of {})'.format(account['_account_id'], i, acc_len), end='')
    file = open("{}/{}".format(accounts_dir, account['_account_id']), "w")
    file.write(")]}'\n")
    file.write(json.dumps(gerrit.get('/accounts/{}'.format(account['_account_id'])), indent=2))
    file.write('\n')
    file.close()
print('\nFetching projects...')
def repo_fetch(project):
    project_stats_dir = os.path.join(stats_dir,project)
    if not os.path.exists(project_stats_dir):
        os.makedirs(project_stats_dir)
    repodir = os.path.join(projects_dir,project+'.git')
    print('\r', end='')
    sys.stdout.write("\033[K")
    print('\rFetching {}'.format(project), end='')
    if os.path.exists(repodir):
        subprocess.call(['git', '-C', repodir, 'fetch', '--quiet', 'origin'], stdout=subprocess.DEVNULL)
    else:
        os.makedirs(repodir)
        if args.mirror and os.path.exists(os.path.join(args.mirror,project+'.git')):
            subprocess.call(['git', 'clone', '-q', '--no-checkout', '--reference', os.path.join(args.mirror,project+'.git'), 'https://github.com/'+project, repodir], stdout=subprocess.DEVNULL)
        else:
            subprocess.call(['git', 'clone', '-q', '--no-checkout', 'https://github.com/'+project, repodir], stdout=subprocess.DEVNULL)

    f = open(os.path.join(project_stats_dir,'all_stats.dat'), 'w')
    subp = subprocess.Popen(['git', '-C', repodir, 'shortlog', '-esn', '--all'], stdout=f, stdin=subprocess.PIPE)
    subp.stdin.close()
    f.close()
    f = open(os.path.join(project_stats_dir,'translation_stats.dat'), 'w')
    subp = subprocess.Popen(['git', '-C', repodir, 'shortlog', '-esn', '--all', '--grep="Automatic translation import"'], stdout=f, stdin=subprocess.PIPE)
    subp.stdin.close()
    f.close()

projects = gerrit.get('/projects/?p=LineageOS')
executor = concurrent.futures.ProcessPoolExecutor(8)
futures = [executor.submit(repo_fetch, project) for project in projects]
concurrent.futures.wait(futures)

print('Generating cloud...')

call(['java -Dfile.encoding=UTF-8 -classpath "./lib/*" CloudGenerator'], shell=True)

print("====================================")
print("== Cloud generated: {}/cloud.zip ==".format(out_dir))
print("====================================")
