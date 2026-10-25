"""Errors a Refresh can raise or record."""


class SourceError(Exception):
    """A Sport's source could not be reached or returned something unexpected.

    The message is shown to Katie in alerts, so keep it short and plain.
    """


class ConfigError(Exception):
    """The Sports config is wrong; the message says which Sport and field."""


class StateError(Exception):
    """The last-good state file can't be read; the message says what to do."""
