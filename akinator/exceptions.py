class ApiException(Exception):
    """Custom exception for API-related errors."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

    def __str__(self):
        return f"{super().__str__()} (status_code: {self.status_code})"
