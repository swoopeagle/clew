from slack_bolt.async_app import AsyncApp

from .lifecycle_builders import (
    AWARDED_CALLBACK_ID,
    DEADLINE_CALLBACK_ID,
    DECLINED_CALLBACK_ID,
)
from .lifecycle_submissions import (
    handle_awarded_submission,
    handle_deadline_submission,
    handle_declined_submission,
)
from .org_profile_builder import ORG_PROFILE_CALLBACK_ID
from .org_profile_submission import handle_org_profile_submission


def register(app: AsyncApp):
    app.view(ORG_PROFILE_CALLBACK_ID)(handle_org_profile_submission)
    app.view(DEADLINE_CALLBACK_ID)(handle_deadline_submission)
    app.view(AWARDED_CALLBACK_ID)(handle_awarded_submission)
    app.view(DECLINED_CALLBACK_ID)(handle_declined_submission)
