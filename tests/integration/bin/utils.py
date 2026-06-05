import typing


def run_cli(main: typing.Callable, *args):
    """Run the a given CLI command with the given arguments.

    Returns the integer exit code.  Use capsys to capture stdout/stderr.
    """
    try:
        main(list(args))
        return 0
    except SystemExit as exc:
        return exc.code or 0
