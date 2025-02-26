import os
import sys

import invoke
from colorama import Fore
from colorama import Style


@invoke.task
def qrc(
    ctx,
):
    """
    Compiles mxGraph and QmxGraph own static web files in Qt resource files.

    This simplifies a lot embedding these contents on Qt web views. It also
    helps freezing an executable, as dependency with static web files becomes
    explicit in Python because of imported resource file.

    Generates 2 resource files located in `qmxgraph` package:

    * `resource_qmxgraph`: static files found in `page/` of QmxGraph;
    * `resource_mxgraph`: static files in mxGraph library, specifically
    all files located in `javascript/src`.

    These resources are imported by QmxGraph widget and must be generated
    before its use.
    """
    import qmxgraph

    from qmxgraph import deploy

    WEB_EXTENSIONS = (
        ".js",
        ".gif",
        ".png",
        ".html",
        ".css",
        ".txt",  # used by mxGraph resources
        ".xml",  # used by mxGraph resources
    )

    indent = "  "
    print_message("qrc", color=Fore.BLUE, bright=True)

    def create_web_resource(resource_name, src_dir):
        print_message(
            "{}- resource: {}".format(indent, resource_name), color=Fore.BLUE, bright=True
        )

        target_dir = os.path.dirname(qmxgraph.__file__)
        qrc_file, py_file = generate_qrc_from_folder(
            basename="resource_{}".format(resource_name),
            alias=resource_name,
            source_dir=src_dir,
            target_dir=target_dir,
            include=WEB_EXTENSIONS,
        )
        print_message("{}* generated {}".format(indent * 2, qrc_file))
        print_message("{}* generated {}".format(indent * 2, py_file))

    mxgraph = os.environ.get("MXGRAPHPATH", None)
    if mxgraph is not None:
        if not os.path.isdir(mxgraph):
            raise IOError(
                "Unable to determine MxGraph to use:"
                " directory obtained from `MXGRAPHPATH` env var does not exist"
            )

    else:
        env_dir = deploy.get_conda_env_path()
        if env_dir is None:
            raise IOError(
                "Unable to determine MxGraph to use:"
                " no `MXGRAPHPATH` env var defined"
                " and no conda environment active"
            )

        mxgraph = "{env_dir}/mxgraph".format(env_dir=env_dir)
        if not os.path.isdir(mxgraph):
            raise IOError(
                "Unable to determine MxGraph to use:"
                " no `MXGRAPHPATH` env var defined"
                " and not located in active conda environment"
            )

    create_web_resource(
        resource_name="mxgraph", src_dir="{folder}/javascript/src".format(folder=mxgraph)
    )

    qgraph_root = os.path.dirname(qmxgraph.__file__)
    create_web_resource(
        resource_name="qmxgraph",
        src_dir=os.path.join(qgraph_root, "page"),
    )


@invoke.task(
    help={
        "python-version": (
            "Can be used to define the python version used when creating the work environment"
        ),
    }
)
def docs(ctx, python_version=None):
    """
    Create the documentation html locally.
    """
    import json
    import subprocess
    import tempfile
    from pathlib import Path

    conda_info_json = subprocess.check_output(["conda", "info", "--json"])
    conda_info = json.loads(conda_info_json)
    current_env_name = conda_info["active_prefix_name"]
    if current_env_name in (None, "base"):
        raise invoke.Exit("Activate the project's conda environment first")
    else:
        docs_env_name = f"{current_env_name}-docs"

    new_environ = os.environ.copy()
    new_environ["TEST_QMXGRAPH"] = "0"
    if python_version is not None:
        new_environ["PYTHON_VERSION"] = python_version

    script = [
        "",  # To have a new line at the start (see windows new line).
        f"conda devenv --name {docs_env_name} --file docs_environment.devenv.yml",
        f"conda activate {docs_env_name}",
        "cd docs",
        "sphinx-build . _build -W",
    ]
    if sys.platform == "win32":
        suffix = ".bat"
        new_line = "\n@echo on\ncall "
        command = ["cmd", "/C"]
    else:
        suffix = ".bash"
        new_line = "\n"
        command = ["bash", "-x"]

    script_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        script_file.close()
        script_file = Path(script_file.name)
        script_file.write_text(new_line.join(script))

        command.append(str(script_file))
        subprocess.check_call(command, env=new_environ)
    finally:
        script_file.unlink()


@invoke.task
def test(ctx):
    print_message("test".format(), color=Fore.BLUE, bright=True)
    cmd = "pytest --cov=qmxgraph --timeout=30 -v --durations=10 --color=yes"

    import subprocess

    raise invoke.Exit(subprocess.call(cmd, shell=True))


@invoke.task
def linting(ctx):
    print_message("lint".format(), color=Fore.BLUE, bright=True)
    cmd = "flake8 -v qmxgraph"

    import subprocess

    raise invoke.Exit(subprocess.call(cmd, shell=True))


@invoke.task(
    help={
        "svg_path": "A SVG file",
    }
)
def svgtostencil(ctx, svg_path):
    """
    Converts a SVG file to a stencil file compatible with mxGraph, output is printed in standard
    output.
    """
    qmxgraph_scripts = os.path.join(os.getcwd(), "scripts")

    import subprocess

    svg_to_stencil_script = os.path.join(qmxgraph_scripts, "svg_to_stencil.py")
    raise invoke.Exit(subprocess.call(["python", svg_to_stencil_script, svg_path]))


def generate_qrc(target_filename, file_map):
    """
    Generates a Qt resource collection file. It is an XML file used to specify
    which resource files are to be embedded, using .qrc as extension.

    Consider call below:

    ```python
    generate_qrc("resource.qrc", ["foo/bar.txt", "/home/dent/bar.txt"])
    ```

    It would generate a .qrc file with contents like:

    ```
    <!DOCTYPE RCC>
    <RCC version="1.0">

    <qresource>
        <file alias="foo/bar.txt">/home/dent/bar.txt</file>
    </qresource>

    </RCC>
    ```

    Once compiled to a Python module (see `generate_qrc_py`), developer could
    access resource like this, for instance:

    ```python
    QFile(":/foo/bar.txt")
    ```

    References:
    * http://doc.qt.io/qt-5/resources.html
    * http://pyqt.sourceforge.net/Docs/PyQt5/resources.html

    :param str target_filename: Path of generated resource collection file.
    :param iterable[tuple[str, str]] file_map: A list of pairs. Each
        pair must be formed by, respectively, alias for file in resource
        collection and path of file to be included in resource collection.
    """
    target_dir = os.path.dirname(target_filename)
    contents = generate_qrc_contents(file_map, target_dir)

    # UTF-8 is the encoding adopted by Qt (and subsequently PyQt) resource
    # collection tools. It seems to not be officially stated anywhere in docs
    # unfortunately, but if it is possible to see this encoding in use by
    # Python modules generated by `pyrcc5`, for instance. Also one moderator
    # in a Qt official forum stated UTF-8 is Qt preference, which is the
    # closest thing to a official documentation about this choice (
    # https://forum.qt.io/topic/42641/the-qt-resource-system-compile-error/4).
    import io

    with io.open(target_filename, "w", encoding="utf8") as f:
        f.write(contents)


def generate_qrc_contents(file_map, target_dir):
    """
    Generates just the contents of a Qt resource collection file. See
    `generate_qrc` for more details.

    :param iterable[tuple[str, str]] file_map: See `generate_qrc`.
    :param str target_dir: The tool that compiles QRC to a Python module
        requires files in QRC to be relative to its execution.
    :rtype: str
    :return: Contents of a resource collection file.
    """
    # Relative paths on Windows can be a pain in the ass if virtual drives
    # (through `subst` command) are used. This make sure all files are
    # using their *actual* absolute path.
    target_dir = follow_subst(target_dir)

    def create_entry(alias_, path_):
        path_ = follow_subst(path_)
        rel_path = os.path.relpath(path_, target_dir)
        return "    " + QRC_ENTRY_TEMPLATE.format(alias=alias_, path=rel_path)

    entries = "\n".join([create_entry(alias, path) for (alias, path) in file_map])
    return QRC_FILE_TEMPLATE.format(entries=entries)


def generate_qrc_py(qrc_filename, target_filename):
    """
    Generates a Python module that only needs to be imported by a Qt
    application in order for those resources to be made available just as if
    they were the original files.

    References:
    * http://doc.qt.io/qt-5/resources.html
    * http://pyqt.sourceforge.net/Docs/PyQt5/resources.html

    :param str qrc_filename: A .qrc resource collection file.
    :param str target_filename: Path of generated Python module.
    """
    import subprocess

    cwd, local_filename = os.path.split(qrc_filename)

    # Needs to be executed on same *actual* absolute path as generated
    # contents, so it also needs to deal with subst.
    cwd = follow_subst(cwd)
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "PyQt5.pyrcc_main",
            local_filename,
            "-o",
            target_filename,
        ],
        cwd=cwd,
    )


def generate_qrc_from_folder(basename, alias, source_dir, target_dir, include=None):
    """
    Collect files from a folder, include them in a resource collection file and
    then compiles it to a Python module.

    All collected files are aliased in resource collection with relative path
    in source dir prefixed by `alias`.

    For instance, consider folder below:

    ```
    - /home/dent/foo/
        * file1.txt
        * file2.txt
        - bar/
            * file3.txt
    ```

    With a call like:

    ```python
    generate_qrc_from_folder("resource_foo", "rsc_foo", "/home/dent/foo/", "/home/dent/foo/")
    ```

    It would result in a .qrc like:

    ```
    <!DOCTYPE RCC>
    <RCC version="1.0">

    <qresource>
        <file alias="rsc_foo/file1.txt">/home/dent/foo/file1.txt</file>
        <file alias="rsc_foo/file2.txt">/home/dent/foo/file2.txt</file>
        <file alias="rsc_foo/bar/file3.txt">/home/dent/foo/bar/file3.txt</file>
    </qresource>

    </RCC>
    ```

    :param str basename: Basename used for .qrc and .py files generated
        for resource collection.
    :param str alias: Basename used for aliases in .qrc file.
    :param str source_dir: Folder that will have its files included in
        resource collection.
    :param str target_dir: Folder where generated .qrc and .py files are
        going to be written.
    :param iterable|None include: Allowed extensions to be collected, if None
        all are allowed.
    """
    if not os.path.isdir(source_dir):
        raise IOError("Invalid source directory: {}".format(source_dir))

    if not os.path.isdir(target_dir):
        raise IOError("Invalid target directory: {}".format(target_dir))

    if sys.platform.startswith("win"):

        def fix_alias(a):
            return a.replace("\\", "/")

    else:

        def fix_alias(a):
            return a

    files = [
        (
            fix_alias(
                "{alias}/{rel_file}".format(alias=alias, rel_file=os.path.relpath(f, source_dir))
            ),
            f,
        )
        for f in collect_files_in_folder(source_dir, include=include)
    ]
    if not files:
        raise RuntimeError(
            "Unable to collect anything for .qrc file in folder {}".format(source_dir)
        )

    qrc_filename = os.path.join(target_dir, "{basename}{ext}".format(basename=basename, ext=".qrc"))
    generate_qrc(qrc_filename, files)

    py_filename = os.path.join(target_dir, "{basename}{ext}".format(basename=basename, ext=".py"))
    generate_qrc_py(qrc_filename, py_filename)

    return qrc_filename, py_filename


def collect_files_in_folder(folder, include=None):
    collected = []
    for root, dirs, files in os.walk(folder):
        for file_ in files:
            if include is None or os.path.splitext(file_)[1] in include:
                collected.append(os.path.normpath(os.path.join(root, file_)))

    return collected


def print_message(message, color=None, bright=True, endline="\n"):
    """
    Print a message to the standard output.

    :param unicode message: The message to print.
    :param unicode|None color: The ANSI color used to colorize the message
        (see `colorama.Fore`). When `None` the message is printed as is.
        Defaults to `None`.
    :param bool bright: Control if the output message is bright or dim. This
        value is ignored if `color is None`. Default to `True`.
    :param unicode endline: The character printed after `message`. Default to
        "new line character".
    """
    import sys

    if color is not None:
        style = Style.BRIGHT if bright else Style.DIM
        message = "{color}{style}{msg}{reset}".format(
            color=color,
            style=style,
            reset=Style.RESET_ALL,
            msg=message,
        )

    # The subprocesses are going to write directly to stdout/stderr, so we
    # need to flush to make sure the output does not get out of order
    sys.stdout.flush()
    sys.stderr.flush()
    print(message, end=endline)
    sys.stdout.flush()
    sys.stderr.flush()


if sys.platform.startswith("win"):

    def follow_subst(path, deep=True):
        """
        Windows has support for virtual drives through `subst` command (
        https://www.microsoft.com/resources/documentation/windows/xp/all/proddocs/en-us/subst.mspx?mfr=true)

        Unfortunately Python doesn't acknowledge that and functions like
        `os.path.relpath` may fail if files in valid relative paths are
        mounted in different virtual drives.

        This function detects all virtual drives on system and replaces one or
        all virtual drives in path (depending on `deep` argument), returning
        actual absolute path.

        :param str path: A path.
        :param bool deep: If should follow all virtual drives on just the
            first one.
        :rtype: str
        :return: Absolute path with virtual drives replaced by actual driver.
        """
        import os

        path = os.path.abspath(path)
        while True:
            drive = path[0] + ":"
            universal_drive = drive.lower()
            subst = parse_subst()
            if universal_drive in subst:
                path = path.replace(drive, subst[universal_drive], 1)
            else:
                break

            if not deep:
                break

        return path

    def parse_subst():
        import re
        import subprocess

        output = subprocess.check_output("subst")

        def parse_subst_line(line):
            import locale

            if not isinstance(line, str):
                line = line.decode(locale.getpreferredencoding(False))

            match = re.match(r"^(\w:)\\: => (.+)$", line)
            drive = match.group(1)
            replace = match.group(2)
            return drive.lower(), replace

        return dict([parse_subst_line(line) for line in output.splitlines()])

else:

    def follow_subst(path, deep=True):
        """
        Noop, only Windows has virtual drives.

        :param str path: A path.
        :param bool deep: If should follow all virtual drives on just the
            first one.
        :rtype: str
        :return: Path as it is.
        """
        return path


QRC_ENTRY_TEMPLATE = '<file alias="{alias}">{path}</file>'
QRC_FILE_TEMPLATE = """\
<!DOCTYPE RCC>
<RCC version="1.0">

<qresource>
{entries}
</qresource>

</RCC>"""


# Only task registered in this global collection will be detected by invoke.
ns = invoke.Collection()
ns.add_task(qrc)
ns.add_task(docs)
ns.add_task(test)
ns.add_task(linting)
ns.add_task(svgtostencil)
