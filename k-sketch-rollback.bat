::This file is meant to allow quick rollbacks in the event of bad updates.
C:

::Navigate to location of GAE Installation
cd Program Files (x86)\Google\google_appengine\ ::Change as necessary

::Location of repository containing application config file (app.yaml)
appcfg.py rollback "D:\My Crap\Work\SMU\FYP\Repository\k-sketch-test" ::Change as necessary

@pause