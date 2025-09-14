class AppBaseError(Exception):
  """Base exception for all application-specific errors."""

  def __init__(self, message: str):
    self.message = message
    super().__init__(self.message)

class DuplicateResourceError(AppBaseError):
  """Raised when attempting to create a resource that already exists."""
  pass

class ExternalAPIError(AppBaseError):
  """Raised when an external API call fails."""
  pass

class ResourceNotFoundError(AppBaseError):
  """Raised when a requested resource is not found."""

  def __init__(self, resource_type: str, resource_id: int | str):
    message = f"{resource_type} with ID '{resource_id}' not found."
    super().__init__(message)
    self.resource_type = resource_type
    self.resource_id = resource_id

class InvalidStateError(AppBaseError):
  """Raised when an operation is attempted in an invalid state."""
  pass

class ConfigValidationError(AppBaseError):
  pass