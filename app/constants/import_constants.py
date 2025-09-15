"""Constants for import operations."""

# Import request statuses
PROCESSING_STATUS = "processing"
COMPLETED_STATUS = "completed"
COMPLETED_WITH_ERRORS_STATUS = "completed_with_errors"
FAILED_STATUS = "failed"

# Import request item statuses
SUCCESS_STATUS = "success"
FAILED_ITEM_STATUS = "failed"

# List of all valid import request statuses
VALID_IMPORT_REQUEST_STATUSES = [
    PROCESSING_STATUS,
    COMPLETED_STATUS,
    COMPLETED_WITH_ERRORS_STATUS,
    FAILED_STATUS,
]

# List of all valid import request item statuses
VALID_IMPORT_ITEM_STATUSES = [
    SUCCESS_STATUS,
    FAILED_ITEM_STATUS,
]

# Status data for API responses
IMPORT_REQUEST_STATUSES_DATA = [
    {"id": PROCESSING_STATUS, "name": "Processing"},
    {"id": COMPLETED_STATUS, "name": "Completed"},
    {"id": COMPLETED_WITH_ERRORS_STATUS, "name": "Completed with Errors"},
    {"id": FAILED_STATUS, "name": "Failed"},
]

IMPORT_ITEM_STATUSES_DATA = [
    {"id": SUCCESS_STATUS, "name": "Success"},
    {"id": FAILED_ITEM_STATUS, "name": "Failed"},
]


class ImportRequestStatuses:
    """Import request status constants."""

    PROCESSING = "processing"
    PENDING = "pending"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"

    @classmethod
    def get_all(cls):
        return [
            cls.PROCESSING,
            cls.PENDING,
            cls.COMPLETED,
            cls.COMPLETED_WITH_ERRORS,
            cls.FAILED,
        ]


class ImportItemStatuses:
    """Import item status constants."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

    @classmethod
    def get_all(cls):
        return [cls.SUCCESS, cls.FAILED]
