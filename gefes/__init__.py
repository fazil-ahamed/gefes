b'This module needs Python 2.6 or later.'

# Special variables #
__version__ = '0.0.1'

# Built-in modules #
import os, sys, glob

# Internal modules #
from gefes.common import dependencies
from gefes.groups.pools import Pool
from gefes.groups.runs import Run, Runs
from gefes.groups.projects import Project, Projects
from gefes.groups.aggregate import Aggregate

# Constants #
home = os.environ['HOME'] + '/'

###############################################################################
# Check dependencies #
dependencies.check_modules()
dependencies.check_executables()

# Output directory #
view_dir = home + 'GEFES/views/'

# Get paths to module #
self = sys.modules[__name__]
module_dir = os.path.dirname(self.__file__)
repos_dir = os.path.abspath(module_dir + '/../') + '/'
pools_dir = repos_dir + 'pools/'

# Load all pools #
json_paths = glob.glob(pools_dir + '*.json')
pools = [Pool(j, view_dir + 'pools/') for j in json_paths]
pools.sort(key=lambda x: str(x))

# Compose into runs #
run_nums = sorted(list(set([p.run_num for p in pools])))
runs = [Run(num, [p for p in pools if p.run_num==num], view_dir + 'runs/') for num in run_nums]
runs = Runs(runs)
for p in pools: p.run = runs[p.run_num]

# Compose into projects #
proj_names = sorted(list(set([p.project_short_name for p in pools])))
projects = [Project(name, [p for p in pools if p.project_short_name==name], view_dir + 'projects/') for name in proj_names]
projects = Projects(projects)
for p in pools: p.project = projects[p.project_short_name]

# Make an aggregate with all pools #
aggregate = Aggregate('all', pools, view_dir + 'aggregates/')

# Call the second init on the pools #
for p in pools: p.load()