"""
signals.py

Defines Django signal handlers for model events within the application.
Handles actions such as creating default dashboards and navlets when new Accounts
 are created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .profiles import Account, AccountDashboard, AccountNavlet


@receiver(post_save, sender=Account)
def create_default_dashboard(sender, instance, created, **_kwargs):
    """
    Signal handler that creates a default dashboard and navlets for a new Account.
    """
    if created:
        dashboard = AccountDashboard.objects.create(
            name='My dashboard', account=instance, num_columns=4, is_default=True
        )
        default_navlets = AccountNavlet.objects.filter(account_id=0)
        for navlet in default_navlets:
            AccountNavlet.objects.create(
                account=instance,
                navlet=navlet.navlet,
                order=navlet.order,
                column=navlet.column,
                preferences=navlet.preferences,
                dashboard=dashboard,
            )
