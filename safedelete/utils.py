from django.contrib.admin.util import NestedObjects

# FIXME: Normally we must be able to use the django Collector, not the NestedObject
#        of the admin.
#        but the django collector returns only the objects we give it, nothing more.
#        Bug ?

def count_related_objects(obj):
    """ Count the objects that would be deleted if we delete "obj" (excluding obj) """
    collector = NestedObjects(using=obj._default_manager._db)
    collector.collect([obj])

    def count_nested(elem):
        if isinstance(elem, list):
            return sum(count_nested(i) for i in elem)
        else:
            return int(obj != elem)

    return count_nested(collector.nested())

