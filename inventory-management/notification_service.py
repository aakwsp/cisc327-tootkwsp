"""Notification simulator Assignment 3.

Place this file beside run.py in your selected project folder, then use
``import notification_service`` from application code.

This module does not send real emails or make network calls. Successful
notifications are stored in memory and disappear when Python exits. It is
a teaching simulator for a single process, not a production delivery system.
The application decides when to notify someone and how to handle failure.

Examples of recipients in the supplied templates:
    Library:          member.email
    Equipment rental: renter.email
    Inventory:        supplier.contact_email or a chosen staff address

For application tests, stub send_notification to return True or False, or
mock it to verify the recipient, subject, and message. Assert the resulting
application behavior too. Patch the dependency where your application uses it.
Use clear_notifications before and after tests that use the real simulator.
"""

SENDER_NAME = "Harborview Hardware Supply - Inventory Team"

_notifications = []


def is_service_available() -> bool:
    """Return True for this local simulator.

    Tests may stub this function to return False to simulate an outage.
    No external service is contacted and no random failures are introduced.
    """
    return True


def send_notification(recipient: str, subject: str, message: str) -> bool:
    """Record a simulated notification and return True on success.

    Return False without recording anything if any argument is not a string,
    is empty/whitespace-only, or the simulated service is unavailable.
    A recipient is a nonempty string (for example, an email or staff label);
    this simulator does not validate email addresses or actual deliverability.
    Valid values are stored exactly as supplied. Repeated sends are recorded
    separately. True means recorded by the simulator, not delivered by email.
    """
    if not all(isinstance(value, str) and value.strip()
               for value in (recipient, subject, message)):
        return False

    if not is_service_available():
        return False

    _notifications.append({
        "sender": SENDER_NAME,
        "recipient": recipient,
        "subject": subject,
        "message": message,
    })
    return True


def get_notifications() -> list:
    """Return all recorded notifications in sending order.

    Return copies of the records so callers cannot modify the stored history.
    Each record has sender, recipient, subject, and message string fields.
    """
    return [notification.copy() for notification in _notifications]


def clear_notifications() -> None:
    """Remove all recorded notifications, for example between test cases."""
    _notifications.clear()
