from django import forms

from nav.models.threshold import Threshold

class ThresholdForm(forms.ModelForm):
    class Meta:
        model = Threshold
