from django.db import models
from django.core.validators import MinLengthValidator

from nav.models.fields import VarcharField


class OUI(models.Model):
    """Defines an OUI and the name of the vendor the OUI belongs to"""

    vendor = VarcharField()
    oui = models.CharField(
        max_length=6, unique=True, validators=[MinLengthValidator(6)]
    )

    def __str__(self):
        return self.oui

    class Meta(object):
        db_table = 'oui'
