"""Constants for membership roles."""

OWNER_ROLE = "owner"
ADMIN_ROLE = "administrator"
COLLABORATOR_ROLE = "collaborator"
PROJECT_MEMBER_ROLE = "project_member"

# List of all valid roles
VALID_ROLES = [OWNER_ROLE, ADMIN_ROLE, COLLABORATOR_ROLE, PROJECT_MEMBER_ROLE]

# Role data for API responses
ROLES_DATA = [
    {"id": OWNER_ROLE, "name": "Owner"},
    {"id": ADMIN_ROLE, "name": "Administrator"},
    {"id": COLLABORATOR_ROLE, "name": "Collaborator"},
    {"id": PROJECT_MEMBER_ROLE, "name": "Project member"},
]


class MembershipRoles:
    OWNER = "owner"
    ADMIN = "admin"
    COLLABORATOR = "collaborator"
    PROJECT_MEMBER = "project_member"

    @classmethod
    def get_all(cls):
        return [cls.OWNER, cls.ADMIN, cls.COLLABORATOR, cls.PROJECT_MEMBER]


class ProjectMembershipRoles:
    ADMIN = "admin"
    COLLABORATOR = "collaborator"

    @classmethod
    def get_all(cls):
        return [cls.ADMIN, cls.COLLABORATOR]
