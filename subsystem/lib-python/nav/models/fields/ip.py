from IPy import IP

from django.core.exceptions import ValidationError
from django.db import models

class InetAddressField(models.Field):
    description = "Postgresql inet field"
    __metaclass__ = models.SubfieldBase

    def db_type(self):
        return 'inet'

    def to_python(self, value):
        if not value:
            return None
        try:
            value = IP(value)
        except Exception, e:
            raise ValidationError(e)
        return value

    def get_db_prep_value(self, value):
        return unicode(self.to_python(value))

class CidrAddressField(InetAddressField):
    description = "Postgresql cidr field"
    __metaclass__ = models.SubfieldBase

    def db_type(self):
        return 'cidr'

class MacAddressField(models.Field):
    description = "Postgresql macaddr field"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 17
        super(MacAddressField, self).__init__(*args, **kwargs)

    def db_type(self):
        return 'macaddr'
