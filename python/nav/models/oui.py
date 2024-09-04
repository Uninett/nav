from django.db import models

from nav.models.fields import VarcharField


class OUI(models.Model):
    """Defines an OUI and the name of the vendor the OUI belongs to"""

    oui = models.CharField(max_length=17, primary_key=True)
    vendor = VarcharField()

    def __str__(self):
        return self.oui

    class Meta(object):
        db_table = 'oui'
