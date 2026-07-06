from typing import Any, Dict

import pytest


@pytest.fixture
def default_showcase_proposal_data() -> Dict[str, Any]:
    return {
        "applicant_full_name": "Mr Json",
        "category": "app",
        "license_type": "free",
        "title": "test",
        "notes": "notes...",
        "url": "https://example.com",
        "applicant_email": "user@example.com",
        "author": "Eric Idle",
        "is_personal_data_processing_accepted": True,
        "is_terms_of_service_accepted": True,
        "is_mobile_app": True,
        "keywords": ["test"],
        "mobile_apple_url": "https://example.com",
        "mobile_google_url": "https://example.com",
        "is_desktop_app": True,
        "desktop_linux_url": "https://example.com",
        "desktop_macos_url": "https://example.com",
        "desktop_windows_url": "https://example.com",
        "external_datasets": [{"title": "example.com", "url": "https://example.com"}],
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpw"
        "YAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAACoSURBVHgB1ZLBDcIwDEWf3XJCQt2AMAEZgU0YgZEYgRUyAit0"
        "gnKnSnCjckA0OXBAqqVIjq1v+399oRbXoWP7dKAeEYfqnoTlOFlswoMUBdFLaWbLjgE2n1Uh2OS+dozyY/wf2BqXsFC/m"
        "zATx1QGvncmU5L8IMYeTZY31DaevqqNhgwWziXgqlRVDow44+qQOFnuOAslNWC1yc18PGZTd+ZdPw/t7O9fCJAsfc2rOZ"
        "EAAAAASUVORK5CYII=",
        "illustrative_graphics": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXM"
        "AAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAACoSURBVHgB1ZLBDcIwDEWf3XJCQt2AMAEZ"
        "gU0YgZEYgRUyAit0gnKnSnCjckA0OXBAqqVIjq1v+399oRbXoWP7dKAeEYfqnoTlOFlswoMUBdFLaWbLjgE2n1Uh2OS+d"
        "ozyY/wf2BqXsFC/mzATx1QGvncmU5L8IMYeTZY31DaevqqNhgwWziXgqlRVDow44+qQOFnuOAslNWC1yc18PGZTd+ZdPw"
        "/t7O9fCJAsfc2rOZEAAAAASUVORK5CYII=",
    }
