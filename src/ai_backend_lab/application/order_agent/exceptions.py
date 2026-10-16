class AgentMaxStepsExceededError(Exception):
    pass


class AgentRunNotFoundError(Exception):
    pass


class AgentRunConflictError(Exception):
    pass


class AgentRunStateError(Exception):
    pass


class ToolExecutionConflictError(Exception):
    pass


class ToolExecutionIntentConflictError(Exception):
    pass


class ToolExecutionInProgressError(Exception):
    pass


class ToolExecutionUnknownOutcomeError(Exception):
    pass


class ToolExecutionStateError(Exception):
    pass
