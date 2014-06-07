from common.serializers import KLPSerializer
from rest_framework import serializers
from schools.models import School, Boundary, DiseInfo

class SchoolListSerializer(KLPSerializer):

    class Meta:
        model = School
        fields = ('id', 'name',)


class SchoolInfoSerializer(KLPSerializer):
    dise_code = serializers.CharField(source='dise_info_id')
    cluster = serializers.CharField(source='schooldetails.cluster_or_circle.name')
    block = serializers.CharField(source='schooldetails.block_or_project.name')
    district = serializers.CharField(source='schooldetails.district.name')

    type_id = serializers.CharField(source='schooldetails.type_id')
    address_full = serializers.CharField(source='address.full')
    landmark = serializers.CharField(source='address.landmark')
    bus = serializers.CharField(source='address.bus')
    identifiers = serializers.CharField(source='address.get_identifiers')

    mp = serializers.CharField(source="get_mp")
    mla = serializers.CharField(source="get_mla")
    ward = serializers.CharField(source="get_ward")

    class Meta:
        model = School
        fields = ('id', 'name', 'mgmt', 'cat', 'moi', 'sex', 'address_full', 'landmark',
            'identifiers', 'cluster', 'block', 'district', 'bus', "mp", "mla", "ward", 'dise_code', 'type_id',)


class SchoolDemographicsSerializer(KLPSerializer):
    num_boys_dise = serializers.IntegerField(source='dise_info.boys_count')
    num_girls_dise = serializers.IntegerField(source='dise_info.girls_count')

    class Meta:
        model = School
        fields = ('id', 'name', 'sex', 'moi', 'mgmt', 'num_boys_dise', 'num_girls_dise')


class SchoolProgrammesSerializer(KLPSerializer):
    class Meta:
        model = School
        fields = ('id', 'name',)


class SchoolFinanceSerializer(KLPSerializer):
    id = serializers.IntegerField(source="school.id")
    name = serializers.CharField(source="school.name")

    class Meta:
        model = DiseInfo
        fields = ('id', 'name', 'sg_recd', 'sg_expnd')


class SchoolDiseSerializer(KLPSerializer):
    id = serializers.IntegerField(source="school.id")
    name = serializers.CharField(source="school.name")

    class Meta:
        model = DiseInfo
        fields = ('id', 'name', ) + tuple([f.name for f in DiseInfo._meta.fields])


class BoundarySerializer(KLPSerializer):
    type = serializers.CharField(source='get_type')

    class Meta:
        model = Boundary
        fields = ('id', 'name', 'type',)


class SchoolDetailsSerializer(KLPSerializer):
    class Meta:
        model = Boundary
        fields = ('cluster_or_circle', 'block_or_project', 'district')


class SchoolPincodeSerializer(KLPSerializer):
    pincode = serializers.CharField(source='address.pincode')

    class Meta:
        model = School
        fields = ('id', 'name', 'pincode')