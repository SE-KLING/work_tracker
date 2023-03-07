from decimal import Decimal

from django import forms

from work_tracker.apps.tracker.enums import EntryStatus
from work_tracker.apps.tracker.models import Entry


class EntryAdditionForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ("task", "start_time", "end_time", "comment")

    def clean(self):
        cd = self.cleaned_data
        if cd["start_time"] >= cd["end_time"]:
            raise forms.ValidationError(
                {"start_time": "An Entry's start time may not exceed its end time."}
            )
        return self.cleaned_data

    def save(self, commit=True):
        cd = self.cleaned_data
        entry = super().save(commit=False)
        total_time = (cd["end_time"] - cd["start_time"]).total_seconds()
        hours = round(total_time / 3600, 6)
        rate = self.cleaned_data["task"].user.rate
        bill = round(Decimal(hours) * rate, 2)
        entry.total_time, entry.hours, entry.bill = total_time, hours, bill
        entry.status = EntryStatus.COMPLETE
        entry.save()
        return entry
