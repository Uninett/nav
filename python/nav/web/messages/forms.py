#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.forms import ModelForm

from nav.models.msgmaint import Message, MaintenanceTask
from nav.models.msgmaint import MessageToMaintenanceTask

class MessageForm(ModelForm):
    """ Model form class for a Message object """

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)

        # Since the m2m uses through, we need to fetch initial data manually
        initials = []
        tasks = MessageToMaintenanceTask.objects.filter(message=self.instance)
        for task in tasks.all():
            initials.append(task.maintenance_task.pk)
        self.initial['maintenance_tasks'] = initials 

        # Classes for javascript plugin
        self.fields['publish_start'].widget.attrs['class'] = 'datetimepicker'
        self.fields['publish_end'].widget.attrs['class'] = 'datetimepicker'

        # Omit seconds when displaying data
        self.fields['publish_start'].widget.format = '%Y-%m-%d %H:%M'
        self.fields['publish_end'].widget.format = '%Y-%m-%d %H:%M'

    
    class Meta:
        model = Message
        exclude = ['author', 'replaces_message', 'last_changed']

    def save(self, commit=True):
        """ 
        Overriding save method to persist related maintenance tasks
        
        We need to manually update the relations to tasks, since django
        can not handle M2M relations with 'through'

        This method will first delete all the relations to a task and
        then save the updated version. Hack?
        """

        # Save the message
        message = super(MessageForm, self).save(commit=False)
        message.save()

        # Cleanup existing tasks related to message
        MessageToMaintenanceTask.objects.filter(message=message).delete()

        # Save all the relations to tasks
        for task in self.cleaned_data.get('maintenance_tasks'):
            o = MessageToMaintenanceTask(message=message, maintenance_task=task)
            o.save()

        return message
