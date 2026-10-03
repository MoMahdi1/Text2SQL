class AgentError(Exception):
    """Base exception for expected agent failures."""


class ConfigurationError(AgentError):
    """Raised when required runtime configuration is missing."""


class UnsafeSQLError(AgentError):
    """Raised when generated SQL violates the read-only policy."""


class DatabaseExecutionError(AgentError):
    """Raised when a validated query cannot be executed."""

