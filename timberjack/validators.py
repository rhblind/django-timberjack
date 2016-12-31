# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_ipv46_address

from mongoengine import ValidationError


def validate_ip_address(value):
    """
    Make sure value is a valid IPv4 or IPv6 address.
    """
    try:
        validate_ipv46_address(value)
        return value
    except DjangoValidationError as e:
        raise ValidationError(str(e))
