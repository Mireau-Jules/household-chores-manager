from django.core.exceptions import ValidationError


def validate_ascii_email(value):
    """Reject non-ASCII emails, so the case rules in D8 and D12 always hold (D14)."""
    if not value.isascii():
        raise ValidationError(
            'Enter an email address using only ASCII characters.',
            code='non_ascii_email',
        )
