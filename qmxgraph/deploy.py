import os


def get_conda_env_path():
    """
    :rtype: str|None
    :return: Helper method to get path where static resources like mxGraph are
        found in Conda environment. None if Conda environment not available.
    """
    import sys
    conda_prefix = os.environ.get('CONDA_PREFIX', None)
    env_path = None
    if conda_prefix is not None:
        if sys.platform.startswith('win'):
            env_path = conda_prefix
        else:
            env_path = os.path.join(conda_prefix, 'usr', 'local')

    return env_path
