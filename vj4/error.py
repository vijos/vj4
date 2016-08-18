from vj4.model import builtin


class Error(Exception):
  pass


class HashError(Error):
  pass


class InvalidStateError(Error):
  pass


class UserFacingError(Error):
  """Error which faces end user."""

  def to_dict(self):
    return {'name': self.__class__.__name__, 'args': self.args}

  @property
  def http_status(self):
    return 500

  @property
  def template_name(self):
    return 'error.html'

  @property
  def message(self):
    return 'An error has occurred.'


class ForbiddenError(UserFacingError):
  @property
  def http_status(self):
    return 403


class NotFoundError(UserFacingError):
  @property
  def http_status(self):
    return 404

  @property
  def message(self):
    return "Path {0} not found."


class ValidationError(ForbiddenError):
  @property
  def message(self):
    if len(self.args) == 1:
      return 'Field {0} validation failed.'
    elif len(self.args) == 2:
      return 'Field {0} or {1} validation failed.'


class UnknownFieldError(ForbiddenError):
  @property
  def message(self):
    return 'Unknown field {0}.'


class InvalidTokenError(ForbiddenError):
  pass


class VerifyPasswordError(ForbiddenError):
  """Error with the `verify password', not password verification error."""
  @property
  def message(self):
    return "Verify password isn't exactly the same as password."


class UserAlreadyExistError(ForbiddenError):
  @property
  def message(self):
    return "User {0} already exists."


class LoginError(ForbiddenError):
  @property
  def message(self):
    return "Invalid user {0} or password."


class DocumentNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Document {2} not found."


class ProblemDataNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Problem {0} data not found."


class PermissionError(ForbiddenError):
  @property
  def message(self):
    if any((p | builtin.PERM_VIEW) == builtin.PERM_VIEW for p in self.args):
      return "You cannot visit this domain."
    else:
      return "User doesn't have the required permission in this domain."


class PrivilegeError(ForbiddenError):
  @property
  def message(self):
    if any((p | builtin.PRIV_USER_PROFILE) == builtin.PRIV_USER_PROFILE for p in self.args):
      return "You're not logged in."
    else:
      return "User doesn't have the required privilege."


class CsrfTokenError(ForbiddenError):
  pass


class InvalidOperationError(ForbiddenError):
  pass


class AlreadyVotedError(ForbiddenError):
  @property
  def message(self):
    return "You've already voted."


class UserNotFoundError(NotFoundError):
  @property
  def message(self):
    return "User not found."


class InvalidTokenDigestError(ForbiddenError):
  pass


class CurrentPasswordError(ForbiddenError):
  @property
  def message(self):
    return "Your current password isn't what you entered."


class DiscussionCategoryAlreadyExistError(ForbiddenError):
  @property
  def message(self):
    return "Discussion category {1} already exists."


class DiscussionCategoryNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Discussion category {1} not found."


class DiscussionNodeAlreadyExistError(ForbiddenError):
  @property
  def message(self):
    return "Discussion node {1} already exists."


class DiscussionNodeNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Discussion node {1} not found."


class DiscussionNotFoundError(DocumentNotFoundError):
  @property
  def message(self):
    return "Discussion {1} not found."


class MessageNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Message {0} not found."


class DomainNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Domain {0} not found."


class DomainAlreadyExistError(ForbiddenError):
  @property
  def message(self):
    return "Domain {0} already exists."


class ContestAlreadyAttendedError(ForbiddenError):
  @property
  def message(self):
    return "You've already attended this contest."


class ContestNotAttendedError(ForbiddenError):
  @property
  def message(self):
    return "You haven't attended this contest yet."


class ContestStatusHiddenError(ForbiddenError):
  @property
  def message(self):
    return "Contest status is hidden."


class TrainingRequirementNotSatisfiedError(ForbiddenError):
  @property
  def message(self):
    return "Training requirement is not satisfied."


class RecordNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Record {0} not found."


class OpcountExceededError(ForbiddenError):
  @property
  def message(self):
    return "{0} limit exceeded (limit: {2} operations in {1} seconds)."
