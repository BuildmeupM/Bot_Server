"""Email System Module"""
from .email_service import EmailService, EmailPattern, EmailSignature, get_global_email_service, set_global_email_service

__all__ = ['EmailService', 'EmailPattern', 'EmailSignature', 'get_global_email_service', 'set_global_email_service']

