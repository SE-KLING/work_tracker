from django import forms
from django.utils import timezone

from work_tracker.apps.tracker.enums import EntryStatus
from work_tracker.apps.tracker.models import Entry
from work_tracker.apps.utils import calculate_billables


class EntryAdditionForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ("task", "start_time", "end_time", "comment")

    def clean(self):
        cd = self.cleaned_data
        now = timezone.now()
        # Ensure user has not selected datetime beyond current time.
        if cd["start_time"] >= now or cd["end_time"] > now:
            raise forms.ValidationError("The selected start_time/end_time values may not exceed the current time.")
        # Ensure user has not selected a start_time greater than the end_time.
        if cd["start_time"] >= cd["end_time"]:
            raise forms.ValidationError(
                {"start_time": "An Entry's start time may not exceed its end time."}
            )
        return self.cleaned_data

    def save(self, commit=True):
        cd = self.cleaned_data
        entry = super().save(commit=False)
        # Calculate and update billables for Entry
        updated_entry = calculate_billables(entry=entry, start_time=cd['start_time'], end_time=cd['end_time'])
        updated_entry.status = EntryStatus.COMPLETE
        updated_entry.save()
        return updated_entry
