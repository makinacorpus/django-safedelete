"""These test uses models for django"s example for extra fields on many to many
relationships
"""
from django.db import models

from ..models import SafeDeleteModel
from ..fields import SafeDeleteManyToManyField
from .testcase import SafeDeleteTestCase


class Person(models.Model):
    name = models.CharField(max_length=128)


class Group(models.Model):
    name = models.CharField(max_length=128)
    members = SafeDeleteManyToManyField(Person, through="Membership")


# Note: this model is safe deletable
class Membership(SafeDeleteModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    invite_reason = models.CharField(max_length=64)


class ManyToManyIntermediateTestCase(SafeDeleteTestCase):

    def test_many_to_many_with_intermediate(self):
        person = Person.objects.create(name="Great singer")
        group = Group.objects.create(name="Cool band")

        # can"t use group.members.add() with intermediate model
        membership = Membership.objects.create(
            person=person,
            group=group,
            invite_reason="Need a new drummer"
        )

        # group members visible now
        self.assertEqual(group.members.count(), 1)

        # soft-delete intermediate instance
        # so link should be invisible
        membership.delete()
        self.assertEqual(Membership.objects.deleted_only().count(), 1)

        self.assertEqual(group.members.count(), 0)
        self.assertEqual(person.group_set.count(), 0)
