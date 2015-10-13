import time
from datetime import datetime, timedelta

from django.db import transaction
from django.core.management.base import BaseCommand

from ivrs.models import State
from schools.models import School
from stories.models import Story, UserType, Questiongroup, Answer


class Command(BaseCommand):
    args = ""
    help = """Creates csv files for calls happened each day

    ./manage.py generategkacsv"""

    @transaction.atomic
    def handle(self, *args, **options):
        today = datetime.now().date()
        states = State.objects.filter(
            date_of_visit__year=today.year,
            date_of_visit__month=today.month,
            date_of_visit__day=today.day
        )

        date = datetime.now().date().strftime("%d_%b_%Y")
        csv = open("/var/www/dubdubdub/gka-ivrs-csv/"+date+".csv", "w")

        lines = ["Sl. No, School ID, District, Block, Cluster, Telephone, Date Of Visit, Invalid, \
Was the school open?, \
Class visited, \
Was Math class happening on the day of your visit?, \
Which chapter of the textbook was taught?, \
Which Ganitha Kalika Andolana TLM was being used by teacher?, \
Did you see children using the Ganitha Kalika Andolana TLM?, \
Was group work happening in the class on the day of your visit?, \
Were children using square line book during math class?, \
Are all the toilets in the school functional?, \
Does the school have a separate functional toilet for girls?, \
Does the school have drinking water?, \
Is a Mid Day Meal served in the school?"
]

        for (number, state) in enumerate(states):
            try:
                school = School.objects.get(id=state.school_id)
                district = school.admin3.parent.parent.name.replace(',', '-')
                block = school.admin3.parent.name.replace(',', '-')
                cluster = school.admin3.name.replace(',', '-')
            except:
                district = block = cluster = None

            values = [str(number + 1),
                      str(state.school_id),
                      str(district),
                      str(block),
                      str(cluster),
                      str(state.telephone),
                      str(state.date_of_visit.date()),
                      str(state.is_invalid)
            ]
            values = values + [answer for answer in state.answers[1:]]
            values = ",".join(values)
            lines.append(str(values))
                            
        for line in lines:
            csv.write(line+"\n")
