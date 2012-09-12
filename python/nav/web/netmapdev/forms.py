from django import forms

class NetmapDefaultViewForm(forms.Form):
    """Form for setting a global netmap view"""
    map_id = forms.IntegerField(label='Map id to use as global default view')