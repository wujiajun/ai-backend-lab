class RiskServiceUnavailableError(Exception):
    pass


class RiskServiceIntegrationError(Exception):
    pass


class LLMUnavailableError(Exception):
    pass


class LLMRateLimitError(Exception):
    pass


class LLMQuotaExceededError(Exception):
    pass


class LLMIntegrationError(Exception):
    pass


class LLMOutputError(Exception):
    pass
