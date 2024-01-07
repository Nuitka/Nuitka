"""`tqdm` version detector. Precedence: installed dist, git, 'UNKNOWN'."""
try:
    from ._dist_ver import __version__
except ImportError:
    __version__ = "UNKNOWN"
