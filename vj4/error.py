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


class NotFoundError(UserFacingError):
  @property
  def http_status(self):
    return 404


class ValidationError(UserFacingError):
  @property
  def message(self):
    if len(self.args) == 1:
      return 'Field {0} validation failed.'
    elif len(self.args) == 2:
      return 'Field {0} or {1} validation failed.'


class InvalidTokenError(UserFacingError):
  pass


class VerifyPasswordError(UserFacingError):
  """Error with the `verify password', not password verification error."""


class UserAlreadyExistError(UserFacingError):
  @property
  def message(self):
    return "User {0} already exists."


class LoginError(UserFacingError):
  @property
  def message(self):
    return "Invalid user {0} or password."


class DocumentNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Document {0} not found."


class ProblemDataNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Problem {0} data not found."


class PermissionError(UserFacingError):
  @property
  def message(self):
    return "User doesn't have the required permission in this domain."


class PrivilegeError(UserFacingError):
  @property
  def message(self):
    if any((p | builtin.PRIV_USER_PROFILE) == builtin.PRIV_USER_PROFILE for p in self.args):
      return "You're not logged in."
    else:
      return "User doesn't have the required privilege."


class CsrfTokenError(UserFacingError):
  pass


class InvalidOperationError(UserFacingError):
  pass


class AlreadyVotedError(UserFacingError):
  pass


class UserNotFoundError(NotFoundError):
  pass


class InvalidTokenDigestError(UserFacingError):
  pass


class ChangePasswordError(UserFacingError):
  pass


class DiscussionCategoryAlreadyExistError(UserFacingError):
  pass


class DiscussionCategoryNotFoundError(NotFoundError):
  pass


class DiscussionNodeAlreadyExistError(UserFacingError):
  pass


class DiscussionNodeNotFoundError(NotFoundError):
  pass


class DiscussionNotFoundError(DocumentNotFoundError):
  @property
  def message(self):
    return "Discussion {0} not found."


class MessageNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Message {0} not found."


class DomainNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Domain {0} not found."


class DomainAlreadyExistError(UserFacingError):
  @property
  def message(self):
    return "Domain {0} already exists."


class ContestAlreadyAttendedError(UserFacingError):
  pass


class ContestNotAttendedError(UserFacingError):
  pass


class ContestStatusHiddenError(UserFacingError):
  @property
  def message(self):
    return "Contest status is hidden."


class TrainingRequirementNotSatisfiedError(UserFacingError):
  pass


class RecordNotFoundError(NotFoundError):
  @property
  def message(self):
    return "Record {0} not found."
