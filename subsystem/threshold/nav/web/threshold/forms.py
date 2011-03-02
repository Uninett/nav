from django import forms

#from nav.models.threshold import Threshold
from nav.models.rrd import RrdDataSource

#class ThresholdForm(forms.ModelForm):
#    class Meta:
#        model = Threshold
class RrdDataSourceForm(forms.ModelForm):
    class Meta:
        model = RrdDataSource

