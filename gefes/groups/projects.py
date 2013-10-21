# Built-in modules #

# Internal modules #
from aggregate import Collection, Aggregate
from gefes.common.autopaths import AutoPaths

# Third party modules #

###############################################################################
class Projects(Collection):
    """A collection of projects."""
    pass

###############################################################################
class Project(Aggregate):
    """A project containing several pools possibly spanning several runs."""

    def __repr__(self): return '<%s object "%s" with %i pools>' % \
                               (self.__class__.__name__, self.name, len(self))

    @property
    def long_name(self): return self.first.project_long_name

    def __init__(self, name, pools, projs_dir):
        # Attributes #
        self.name = name
        self.pools, self.children = pools, pools
        # Dir #
        self.base_dir = projs_dir + self.name + '/'
        self.p = AutoPaths(self.base_dir, self.all_paths)
        # Common init stuff #
        self.load()