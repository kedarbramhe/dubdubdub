import time
import operator
from optparse import make_option
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.contrib.auth.models import Group
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand

from ivrs.models import State
from users.models import User
from schools.models import School, Boundary
from common.utils import send_attachment, Date
from stories.models import Story, UserType, Questiongroup, Answer

EXCLUDED_DISTRICTS = [
    'bangalore',
    'bangalore u south',
    'koppal',
    'mysore',
    'kolar',
    'chamrajnagar',
    'belgaum',
    'bangalore u north',
    'ramnagara',
    'dharwad',
]

EXCLUDED_DISTRICT_IDS = [431, 8877, 8878, 444, 413, 421, 419, 439, 9540, 9541]

EXCLUDED_BLOCKS = [
    'hunagund',
    'magadi',
    'ramanagara',
    'kanakapura',
    'kudligi',
    'kollegal',
    'south-1',
    'south-3',
    'north-1',
    'north-2',
    'north-4',
    'north-3',
    'mysore south',
    'koppal',
    'bangarapete',
    'bangalore south(banashankari)',
    'sumangali seva ashrama',
    'bangalore north (yelahanka)',
    'belgaum city',
    'badami',
    'bagalkot',
    'bilagi',
    'jamakhandi',
    'mudhol',
    'yelandur',
    'dharwad',
    'kundagol'
]

EXCLUDED_BLOCK_IDS = [8882, 8886, 573, 464, 502, 465, 466, 493, 530, 505, 650, 467, 8889, 651, 626, 5999, 653, 462, 457, 463, 625, 8883, 8884, 8879, 8881, 8776, 8774, 8779]

class Command(BaseCommand):
    args = ""
    help = """Creates csv files for calls happened each day

    ./manage.py generategkacsv [--duration=monthly/weekly] [--from=YYYY-MM-DD] [--to=YYYY-MM-DD] [--fc_report=True/False] --emails=a@b.com,c@d.com"""

    option_list = BaseCommand.option_list + (
        make_option('--from',
                    help='Start date'),
        make_option('--to',
                    help='End date'),
        make_option('--duration',
                    help='To specify whether it is a monthly or weekly csv'),
        make_option('--emails',
                    help='Comma separated list of email ids'),
        make_option('--fc_report',
                    help='Whether to generate BFC and CRP reports'),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        duration = options.get('duration', None)
        start_date = options.get('from', None)
        end_date = options.get('to', None)
        emails = options.get('emails', None)
        fc_report = options.get('fc_report', None)

        today = datetime.now().date()
        if duration:
            if duration == 'weekly':
                days = 7
            elif duration == 'monthly':
                days = 30
            start_date = today - timedelta(days=int(days))
            end_date = today

        elif (start_date and end_date):
            date = Date()
            sane = date.check_date_sanity(start_date)
            if not sane:
                print """
                Error:
                Wrong --from format. Expected YYYY-MM-DD
                """
                print self.help
                return
            else:
                start_date = date.get_datetime(start_date)

            sane = date.check_date_sanity(end_date)
            if not sane:
                print """
                Error:
                Wrong --to format. Expected YYYY-MM-DD
                """
                print self.help
                return
            else:
                end_date = date.get_datetime(end_date)
        else:
            raise Exception(
                "Please specify --duration as 'monthly' or 'weekly' OR --from and --to"
            )

        if not emails:
            raise Exception(
                "Please specify --emails as a list of comma separated emails"
            )
        emails = emails.split(",")
        
        report_dir = settings.PROJECT_ROOT + "/gka-reports/"

        bfc = Group.objects.get(name="BFC")
        crp = Group.objects.get(name="CRP")
        bfc_users = bfc.user_set.all()
        crp_users = crp.user_set.all()
        
        states = State.objects.filter(
            date_of_visit__gte=start_date,
            date_of_visit__lte=end_date
        )
        valid_states = states.filter(is_invalid=False)

        date = datetime.now().date().strftime("%d_%b_%Y")
        csv_file = report_dir + date + '.csv'
        csv = open(csv_file, "w")

        lines = []

        # Overall count
        heading = "OVERALL COUNT"
        lines.extend([heading, "\n"])

        columns = "Total SMS received, No. of invalid SMS, % of invalid SMS, No. valid SMS received from BFC, No. valid SMS received from CRP, No. of schools with unique valid SMS"
        lines.extend([columns])

        total_sms_received = states.count()
        number_of_invalid_sms = states.filter(is_invalid=True).count()
        percentage_of_invalid_sms = (float(number_of_invalid_sms) / float(total_sms_received)) * 100.0
        number_of_valid_smses_from_bfc = valid_states.filter(user__in=bfc_users).count()
        number_of_valid_smses_from_crp = valid_states.filter(user__in=crp_users).count()
        number_of_schools_with_unique_valid_sms = states.filter(
            is_invalid=False).order_by().distinct('school_id').count()

        values = [
            str(total_sms_received),
            str(number_of_invalid_sms),
            str(percentage_of_invalid_sms),
            str(number_of_valid_smses_from_bfc),
            str(number_of_valid_smses_from_crp),
            str(number_of_schools_with_unique_valid_sms)
        ]

        values = ",".join(values)
        lines.extend([values, "\n"])

        # Invalid SMS error classification
        heading = "INVALID SMS ERROR CLASSIFICATION"
        lines.extend([heading, "\n"])

        columns = "Error type, Count"
        lines.extend([columns])

        errors = states.filter(is_invalid=True).values_list('comments', flat=True)
        errors_dict = {}
        for error in errors:
            # Let's make certain errors more concise. Refer to 'get_message'
            # in utils.py for all possible messages.
            if error:
                if 'Expected' in error:
                    error = 'Formatting error'
                if 'registered' in error:
                    error = 'Not registered'
                if 'que.no' in error:
                    error = 'Entry error for a specific question'
                if 'School' in error:
                    error = 'School ID error'
                if 'Logical' in error:
                    error = 'Logical error'
                if 'accepted' in error:
                    # We have to do this because all State are by default
                    # invalid when created. Since we only process SMSes at
                    # 8.30PM in the night, the SMSes that came in that day
                    # morning will show as invalid.
                    continue
            if error in errors_dict:
                errors_dict[error] += 1
            else:
                errors_dict[error] = 1

        for error, count in errors_dict.iteritems():
            values = [
                str(error),
                str(count)
            ]
            values = ",".join(values)
            lines.extend([values])
        lines.extend(["\n"])


        # District Level performance
        heading = "DISTRICT LEVEL PERFORMANCE"
        lines.extend([heading, "\n"])

        columns = ("District,"
                   "Total SMS received,"
                   "No. SMS from BFC,"
                   "No. SMS from CRP,"
                   "Invalid SMS Count,"
                   "BFC invalid SMS count,"
                   "CRP invalid SMS count,"
                   "No. of unique schools with invalid SMS"
                   )
        lines.extend([columns])

        school_ids = State.objects.all().values_list('school_id', flat=True)
        district_ids = School.objects.filter(
            id__in=school_ids
        ).values_list(
            'admin3__parent__parent', flat=True
        ).order_by(
        ).distinct(
            'admin3__parent__parent'
        )
        districts = Boundary.objects.filter(id__in=district_ids).exclude(id__in=EXCLUDED_DISTRICT_IDS)

        district_dict = {}
        for district in districts:
            school_ids = district.schools().values_list('id', flat=True)
            smses = states.filter(school_id__in=school_ids)
            smses_received = smses.count()
            district_dict[district.id] = smses_received
        district_dict_list = sorted(district_dict.items(), key=operator.itemgetter(1), reverse=True)

        for district_id, smses_count in district_dict_list:
            district = Boundary.objects.get(id=district_id)
            school_ids = district.schools().values_list('id', flat=True)
            smses = states.filter(school_id__in=school_ids)
            smses_received = smses.count()
            smses_from_bfc = smses.filter(user__in=bfc_users).count()
            smses_from_crp = smses.filter(user__in=crp_users).count()
            invalid_smses = smses.filter(is_invalid=True).count()
            invalid_smses_from_bfc = smses.filter(is_invalid=True, user__in=bfc_users).count()
            invalid_smses_from_crp = smses.filter(is_invalid=True, user__in=crp_users).count()
            schools_with_invalid_smses = smses.filter(is_invalid=True).order_by().distinct('school_id').count()

            values = [
                str(district.name),
                str(smses_received),
                str(smses_from_bfc),
                str(smses_from_crp),
                str(invalid_smses),
                str(invalid_smses_from_bfc),
                str(invalid_smses_from_crp),
                str(schools_with_invalid_smses),
            ]

            values = ",".join(values)
            lines.extend([values])


        lines.extend(["\n"])
        # Block Level performance
        heading = "BLOCK LEVEL PERFORMANCE"
        lines.extend([heading, "\n"])

        columns = ("Block,"
                   "District,"
                   "Total SMS received,"
                   "No. SMS from BFC,"
                   "No. SMS from CRP,"
                   "Invalid SMS Count,"
                   "BFC invalid SMS count,"
                   "CRP invalid SMS count,"
                   "No. of unique schools with invalid SMS"
                   )
        lines.extend([columns])

        school_ids = State.objects.all().values_list('school_id', flat=True)
        block_ids = School.objects.filter(
            id__in=school_ids
        ).values_list(
            'admin3__parent', flat=True
        ).order_by(
        ).distinct(
            'admin3__parent'
        )
        blocks = Boundary.objects.filter(id__in=block_ids).exclude(id__in=EXCLUDED_BLOCK_IDS)

        block_dict = {}
        for block in blocks:
            school_ids = block.schools().values_list('id', flat=True)
            smses = states.filter(school_id__in=school_ids)
            smses_received = smses.count()
            block_dict[block.id] = smses_received
        block_dict_list = sorted(block_dict.items(), key=operator.itemgetter(1), reverse=True)

        for block_id, smses_count in block_dict_list:
            block = Boundary.objects.get(id=block_id)
            school_ids = block.schools().values_list('id', flat=True)
            smses = states.filter(school_id__in=school_ids)
            smses_received = smses.count()
            smses_from_bfc = smses.filter(user__in=bfc_users).count()
            smses_from_crp = smses.filter(user__in=crp_users).count()
            invalid_smses = smses.filter(is_invalid=True).count()
            invalid_smses_from_bfc = smses.filter(is_invalid=True, user__in=bfc_users).count()
            invalid_smses_from_crp = smses.filter(is_invalid=True, user__in=crp_users).count()
            schools_with_invalid_smses = smses.filter(is_invalid=True).order_by().distinct('school_id').count()

            values = [
                str(block.name),
                str(block.parent.name),
                str(smses_received),
                str(smses_from_bfc),
                str(smses_from_crp),
                str(invalid_smses),
                str(invalid_smses_from_bfc),
                str(invalid_smses_from_crp),
                str(schools_with_invalid_smses),
            ]

            values = ",".join(values)
            lines.extend([values])

        lines.extend(["\n"])

        # Top 5 valid SMS contributors:
        heading = "TOP 5 VALID SMS CONTRIBUTORS"
        lines.extend([heading, "\n"])

        columns = ("Name,"
                   "Mobile number,"
                   "Districts,"
                   "Blocks,"
                   "Clusters,"
                   "Group,"
                   "Valid SMS count,"
                   "SMS count"
        )
        lines.extend([columns])

        users = User.objects.filter(
            state__in=valid_states
        ).annotate(sms_count=Count('state')).order_by('-sms_count')[:5]

        for user in users:
            name = user.get_full_name()
            mobile_number = user.mobile_no
            school_ids = user.state_set.filter(id__in=valid_states).values_list('school_id',flat=True)
            clusters = School.objects.filter(
                id__in=school_ids
            ).values_list(
                'admin3__name', flat=True
            ).order_by(
            ).distinct(
                'admin3__name'
            )
            blocks = School.objects.filter(
                id__in=school_ids
            ).values_list(
                'admin3__parent__name', flat=True
            ).order_by(
            ).distinct(
                'admin3__parent__name'
            )
            districts = School.objects.filter(
                id__in=school_ids
            ).values_list(
                'admin3__parent__parent__name', flat=True
            ).order_by(
            ).distinct(
                'admin3__parent__parent__name'
            )

            try:
                group = user.groups.get().name
            except:
                group = ''

            valid_smses = states.filter(user=user, is_invalid=False).count()
            total_smses = states.filter(user=user).count()

            values = [
                str(name),
                str(mobile_number),
                str("-".join(districts)),
                str("-".join(blocks)),
                str("-".join(clusters)),
                str(group),
                str(valid_smses),
                str(total_smses)
            ]

            values = ",".join(values)
            lines.extend([values])

        lines.extend(["\n"])

        # Top 5 blocks with valid SMS
        heading = "TOP 5 BLOCKS WITH VALID SMS"
        lines.extend([heading, "\n"])

        columns = ("Block Name,"
                   "District Name,"
                   "Number of Valid SMS,"
        )
        lines.extend([columns])

        school_ids = valid_states.values_list('school_id', flat=True)
        block_ids = School.objects.filter(
            id__in=school_ids
        ).values_list(
            'admin3__parent', flat=True
        ).order_by(
        ).distinct(
            'admin3__parent'
        )
        blocks = Boundary.objects.filter(id__in=block_ids)
        block_sms_dict = {}
        for block in blocks:
            school_ids = block.schools().values_list('id', flat=True)
            smses = valid_states.filter(school_id__in=school_ids).count()
            block_sms_dict[block.id] = smses

        block_sms_list = sorted(block_sms_dict.items(), key=operator.itemgetter(1))
        for i in list(reversed(block_sms_list))[:5]:
            block = Boundary.objects.get(id=i[0])
            values = [
                str(block.name),
                str(block.parent.name),
                str(i[1]),
            ]

            values = ",".join(values)
            lines.extend([values])

        lines.extend(["\n"])

        if fc_report == 'True':

            # Weekly BFC error report
            heading = "BFC ERROR REPORT"
            lines.extend([heading, "\n"])

            columns = ("Group,"
                       "Name,"
                       "Telephone,"
                       "District,"
                       "Block,"
                       "Cluster,"
                       "SMSes sent,"
                       "Number of Invalid SMS,"
                       "Top 3 error classification with counts,"
                       "Number of schools with SMS,"
                       "No. of unique schools with SMS"
            )
            lines.extend([columns])

            user_dict = {}
            for user in bfc_users:
                user_smses_count = user.state_set.filter(id__in=states).count()
                user_dict[user.id] = user_smses_count
            user_dict_list = sorted(user_dict.items(), key=operator.itemgetter(1), reverse=True)

            for user_id, user_smses_count in user_dict_list:
                group = "BFC"
                user = User.objects.get(id=user_id)
                user_smses = user.state_set.filter(id__in=states)
                name = user.get_full_name()
                telephone = user.mobile_no
                school_ids = user_smses.values_list('school_id',flat=True)
                clusters = School.objects.filter(
                    id__in=school_ids
                ).values_list(
                    'admin3__name', flat=True
                ).order_by(
                ).distinct(
                    'admin3__name'
                )
                blocks = School.objects.filter(
                    id__in=school_ids
                ).values_list(
                    'admin3__parent__name', flat=True
                ).order_by(
                ).distinct(
                    'admin3__parent__name'
                )
                districts = School.objects.filter(
                    id__in=school_ids
                ).values_list(
                    'admin3__parent__parent__name', flat=True
                ).order_by(
                ).distinct(
                    'admin3__parent__parent__name'
                )
                smses_sent = user_smses.count()
                invalid_smses_count = user_smses.filter(is_invalid=True).count()
                errors = user_smses.filter(is_invalid=True).values_list('comments', flat=True)
                errors_dict = {}
                for error in errors:
                    if error:
                        if 'Expected' in error:
                            error = 'Formatting error'
                        if 'registered' in error:
                            error = 'Not registered'
                        if 'que.no' in error:
                            error = 'Entry error for a specific question'
                        if 'School' in error:
                            error = 'School ID error'
                        if 'Logical' in error:
                            error = 'Logical error'
                        if 'accepted' in error:
                            # We have to do this because all State are by default
                            # invalid when created. Since we only process SMSes at
                            # 8.30PM in the night, the SMSes that came in that day
                            # morning will show as invalid.
                            continue
                    if error in errors_dict:
                        errors_dict[error] += 1
                    else:
                        errors_dict[error] = 1
                errors_dict = sorted(errors_dict.items(), key=operator.itemgetter(1))
                top_3_errors = list((reversed(errors_dict)))[:3]
                schools_with_sms = user_smses.values_list('school_id',flat=True).count()
                unique_schools_with_sms = user_smses.values_list('school_id',flat=True).order_by().distinct('school_id').count()
                values = [
                    str(group),
                    str(name),
                    str(telephone),
                    str("-".join(districts)),
                    str("-".join(blocks)),
                    str("-".join(clusters)),
                    str(smses_sent),
                    str(invalid_smses_count),
                    str(top_3_errors).replace(',', '-'),
                    str(schools_with_sms),
                    str(unique_schools_with_sms)
                ]
            
                values = ",".join(values)
                lines.extend([values])

            lines.extend(["\n"])

            # Weekly CRP error report
            heading = "CRP ERROR REPORT"
            lines.extend([heading, "\n"])

            columns = ("Group,"
                       "Name,"
                       "Telephone,"
                       "District,"
                       "Block,"
                       "Cluster,"
                       "SMSes sent,"
                       "Number of Invalid SMS,"
                       "Top 3 error classification with counts,"
                       "Number of schools with SMS,"
                       "No. of unique schools with SMS"
            )
            lines.extend([columns])

            user_dict = {}
            for user in crp_users:
                user_smses_count = user.state_set.filter(id__in=states).count()
                user_dict[user.id] = user_smses_count
            user_dict_list = sorted(user_dict.items(), key=operator.itemgetter(1), reverse=True)

            for user_id, user_smses_count in user_dict_list:
                group = "CRP"
                user = User.objects.get(id=user_id)
                user_smses = user.state_set.filter(id__in=states)
                name = user.get_full_name()
                telephone = user.mobile_no
                school_ids = user_smses.values_list('school_id',flat=True)
                clusters = School.objects.filter(
                    id__in=school_ids
                ).values_list(
                    'admin3__name', flat=True
                ).order_by(
                ).distinct(
                    'admin3__name'
                )
                blocks = School.objects.filter(
                    id__in=school_ids
                ).values_list(
                    'admin3__parent__name', flat=True
                ).order_by(
                ).distinct(
                    'admin3__parent__name'
                )
                districts = School.objects.filter(
                    id__in=school_ids
                ).values_list(
                    'admin3__parent__parent__name', flat=True
                ).order_by(
                ).distinct(
                    'admin3__parent__parent__name'
                )
                smses_sent = user_smses.count()
                invalid_smses_count = user_smses.filter(is_invalid=True).count()
                errors = user_smses.filter(is_invalid=True).values_list('comments', flat=True)
                errors_dict = {}
                for error in errors:
                    if error:
                        if 'Expected' in error:
                            error = 'Formatting error'
                        if 'registered' in error:
                            error = 'Not registered'
                        if 'que.no' in error:
                            error = 'Entry error for a specific question'
                        if 'School' in error:
                            error = 'School ID error'
                        if 'Logical' in error:
                            error = 'Logical error'
                        if 'accepted' in error:
                            # We have to do this because all State are by default
                            # invalid when created. Since we only process SMSes at
                            # 8.30PM in the night, the SMSes that came in that day
                            # morning will show as invalid.
                            continue

                    if error in errors_dict:
                        errors_dict[error] += 1
                    else:
                        errors_dict[error] = 1
                errors_dict = sorted(errors_dict.items(), key=operator.itemgetter(1))
                top_3_errors = list((reversed(errors_dict)))[:3]
                schools_with_sms = user_smses.values_list('school_id',flat=True).count()
                unique_schools_with_sms = user_smses.values_list('school_id',flat=True).order_by().distinct('school_id').count()
                values = [
                    str(group),
                    str(name),
                    str(telephone),
                    str("-".join(districts)),
                    str("-".join(blocks)),
                    str("-".join(clusters)),
                    str(smses_sent),
                    str(invalid_smses_count),
                    str(top_3_errors).replace(',', '-'),
                    str(schools_with_sms),
                    str(unique_schools_with_sms)
                ]
            
                values = ",".join(values)
                lines.extend([values])

            lines.extend(["\n"])

        for line in lines:
            csv.write(line+"\n")

        date_range = start_date.strftime("%d/%m/%Y") + " to " + today.strftime("%d/%m/%Y")
        subject = 'GKA SMS Report for '+ date_range
        from_email = settings.EMAIL_DEFAULT_FROM
        to_emails = emails
        msg = EmailMultiAlternatives(subject, "Please view attachment", from_email, to_emails)
        msg.attach_alternative("<b>Please View attachement</b>", "text/html")
        msg.attach_file(csv_file)
        msg.send()

                            
