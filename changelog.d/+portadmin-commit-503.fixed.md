PortAdmin's "commit configuration" endpoint now returns 503 instead of 500 when the
device is unreachable or does not support configuration commits, and no longer triggers
spurious admin error emails for these expected operational failures.
