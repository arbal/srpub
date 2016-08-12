#!/usr/bin/python

from utils import *
import sys, re

class Commit:
    def __init__(self, sha, title):
        self.sha = sha
        self.title = title

def clean_up_decorate(lines):
    res = ''
    for line in lines.split('\n'):
        m = re.search(r'\((.+?)\)', line)
        if m:
            decorate = m.group(1)
            tags = decorate.split(',')
            tags = [t.strip() for t in tags if not t.strip().startswith('deploy_build') and not t.strip().startswith('deployed')]
            if not tags:
                line = line.replace('(' + decorate + ')', '')
            else:
                line = line.replace(decorate, ', '.join(tags))
        res += line + '\n'
    return res

def show_sha(sha):
    res = clean_up_decorate(cmd('git --no-pager log --pretty=format:"%Cgreen%H%Creset   %an %C(yellow)%d%Creset%n   %s%n" -1 ' + sha))
    res = res.replace("Samuel Russell", blue_str("Samuel Russell"))
    print res
    #cmd('git --no-pager show --pretty=format:"%Cgreen%H%Creset   %an%n   %s%n" ' + sha + ' | head -n 3', noisy=True)

def show_shas(sha_first, sha_last):
    res = clean_up_decorate(cmd('git --no-pager log --pretty=format:"%Cgreen%H%Creset   %an %C(yellow)%d%Creset%n   %s%n" ' + sha_first + '...' + sha_last))
    res = res.replace("Samuel Russell", blue_str("Samuel Russell"))
    print res
    return res

def show_my_most_recent(fb):
    print '               ....\n'
    res = clean_up_decorate(cmd('git --no-pager log --author=srussell --pretty=format:"%Cgreen%H%Creset   %an %C(yellow)%d%Creset%n   %s%n" -1 ' + fb))
    res = res.replace("Samuel Russell", blue_str("Samuel Russell"))
    print res

def show_sha_grey(sha):
    res = cmd('git --no-pager log --pretty=format:"%H   %an%n   %s%n%Creset" -1 ' + sha)
    if "Samuel Russell" in res:
        ts = res.split("Samuel Russell")
        print grey_str(ts[0]) + blue_str("Samuel Russell") + grey_str(ts[1])
    else:
        print grey_str(res)
    print ''

def show_sha_magenta(sha):
    res = cmd('git --no-pager log --pretty=format:"%C(magenta)%H%Creset   %an%n   %s%n" -1 ' + sha)
    res = res.replace("Samuel Russell", blue_str("Samuel Russell"))
    print res
    print ''

def fetch_commits_for_branch(branch, n):
    raw = cmd('git log ' + branch + ' --format=oneline -n ' + str(n))
    if 'Not a git repository' in raw:
        print red_str('Not a git repository')
        sys.exit(0)
    res = []
    for l in raw.rstrip().split('\n'):
        if l.startswith('warning'):
            continue
        ls = l.split()
        sha = ls[0]
        title = " ".join(ls[1:])
        if 'These files were automatically checked in' in title:
            title = sha
        c = Commit(sha, title)
        res.append(c)
    return res

###########################################################
#     Fetch info about the branch and remote branch
###########################################################
showall = False
if len(sys.argv) > 1 and sys.argv[1] == '--all':
    showall = True

status = cmd('git status -bs 2>/dev/null').rstrip().split('\n')
if not status or len(status) == 0 or not status[0]:
    print red_str("Not a git repo")
    sys.exit(1)
branchline = status[0] + ' '
m = re.search(r'\.\.\.(.*?) ', branchline)
if m:
    fb = m.group(1)
    branchline = branchline.replace('...', ' ')
    current_branch = branchline.split()[1]
else:
    fb = 'origin'
    current_branch = branchline.split()[1]

###########################################################
#     Fetch the log info about local HEAD and remote branch
###########################################################

second_try = False
tot_n = 100
origin_n = 200

while True:
    tot = fetch_commits_for_branch("", tot_n)
    totsha = [c.sha for c in tot]
    tottitle = [c.title for c in tot]

    if not fb:
        # not a remote-tracking branch
        for c in tot[0:6]:
            show_sha(c.sha)
        sys.exit(1)

    origin = fetch_commits_for_branch(fb, origin_n)
    originsha = [c.sha for c in origin]
    origintitle = [c.title for c in origin]

    # How many commits in each category
    made = [c for c in tot[0:50] if c.title not in origintitle]
    made_merged = [c for c in tot[0:50] if c.title in origintitle and c.sha not in originsha]
    missing = [c for c in origin[0:(tot_n-len(made))] if c.sha not in totsha and c.title not in tottitle]
    common = [c for c in origin if c.sha in totsha and c.title in tottitle]

    if len(made) + len(made_merged) < 15:
        break
    else:
        if second_try:
            # something is wierd
            break
        else:
            tot_n = 1000
            origin_n = 1200
            second_try = True

## Uncomment this line to run a fetch before very call, slower but shows a more accurate state #######
#cmd('git fetch')

###########################################################
#     Print branch info
###########################################################

print
print '******************************************************************'
print blue_str(bold_str('%25s' % current_branch))
other_branches = cmd('git branch').replace('*', '').strip().split('\n')
branch_data = dict()
for branch in other_branches:
    branch = branch.strip()
    if branch == current_branch:
        continue
    try:
        stats = cmd('git show --pretty=format:"%ci %cr" ' + branch + ' -- | head -n 1').split(' ')
        dt = datetime.datetime.strptime(stats[0] + ' ' + stats[1], "%Y-%m-%d %H:%M:%S")
        age = stats[3] + ' ' + stats[4]
    except:
        dt = datetime.datetime.now()
        age = ''
    branch_data[dt] = (branch, age)

for idx, dt in enumerate(sorted(branch_data.keys(), reverse=True)):
    branch, age = branch_data[dt]
    if 'minutes' in age or 'hours' in age:
        age = ''
    print '%25s ' % branch + grey_str('%-10s' % age),
    if idx % 2 == 1:
        print ''
print ''
print '******************************************************************'

###########################################################
#     Print local status diffs
###########################################################
untracked = []
for l in status[1:]:
    if '??' in l:
        untracked.append(l)
    else:
        print l

if len(untracked) > 3:
    print red_str(str(len(untracked)) + ' Untracked files ??')
else:
    for u in untracked:
        print red_str(u)
print ''

###########################################################
#     print commits cherry picked on top
###########################################################
done = 0
cp_but_merged = 0

if len(made) + len(made_merged) > 15:
    # something is wierd
    print red_str("\nUnable to determine alignment with remote\n")
    show_shas(totsha[0], totsha[8])
    sys.exit(1)
    
for c in tot[0:50]:
    if c in made:
        done += 1
        show_sha(c.sha)
    if c in made_merged:
        # Cherry picked and merged
        done += 1
        cp_but_merged += 1
        show_sha_magenta(c.sha)

# usually happens if there is no origin
if len(common) == 0:
    sys.exit(1)

print blue_str("    ********** " + fb + " ************")

###########################################################
#     print commits in origin missing from HEAD'
###########################################################
if len(missing) > 5 and not showall:
    print grey_str('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print grey_str('   ' + str(len(missing)) + ' missing commits')
    print grey_str('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    done += 2
elif len(missing) > 0:
    for c in missing:
        show_sha_grey(c.sha)
        done += 1

###########################################################
#     print merged commits in origin and HEAD
###########################################################

left = max(1, 10-done)
originz = show_shas(common[0].sha, common[left].sha)

###########################################################
#     print my last merged commit if not in the above
###########################################################
if 'Samuel Russell' not in originz:
    show_my_most_recent(fb)