# -*- coding: UTF-8 -*-
import haystack

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from conference import models
from conference.templatetags.conference import fare_blob

from collections import defaultdict
from datetime import datetime

class Command(BaseCommand):
    """
    """
    @transaction.commit_on_success
    def handle(self, *args, **options):
        try:
            conference = args[0]
        except IndexError:
            raise CommandError('conference missing')

        partner_events = defaultdict(list)
        for f in models.Fare.objects.available(conference=conference).filter(ticket_type='partner'):
            try:
                date = datetime.strptime(fare_blob(f, 'data').split(',')[0][:-2] + ' 2011', '%B %d %Y').date()
                time = datetime.strptime(fare_blob(f, 'departure'), '%H:%M').time()
            except ValueError:
                continue
            partner_events[date].append((f, time))

        for sch in models.Schedule.objects.filter(conference=conference):
            events = list(models.Event.objects.filter(schedule=sch))
            for fare, time in partner_events[sch.date]:
                for e in events:
                    track_id = 'f%s' % fare.id
                    if track_id in e.get_all_tracks_names():
                        event = e
                        break
                else:
                    event = models.Event(schedule=sch, talk=None)
                    event.track = 'partner-program ' + track_id
                event.custom = fare.name
                event.start_time = time
                event.duration = 60
                event.save()

