class InvitationException(Exception):
    """Base exception for invitation-related errors."""

    pass


class InvitationNotFoundError(InvitationException):
    """Raised when an invitation is not found."""

    pass


class InvitationExpiredError(InvitationException):
    """Raised when an invitation has expired."""

    pass


class InvitationUnauthorizedError(InvitationException):
    """Raised when a user is not authorized to accept/decline an invitation."""

    pass


class UserNotFoundError(InvitationException):
    """Raised when a user is not found."""

    pass


class InvitationAlreadyAcceptedError(InvitationException):
    """Raised when an invitation has already been accepted."""

    pass


class InvitationAlreadyDeclinedError(InvitationException):
    """Raised when an invitation has already been declined."""

    pass
