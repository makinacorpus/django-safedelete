#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == '__main__':
    print("\n#######################################")
    print("  RUN TESTS WITHOUT BOOLEAN FIELD ")
    print("#######################################\n")

    os.environ['DJANGO_SETTINGS_MODULE'] = 'safedelete.tests.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    tests = ['safedelete.tests'] if len(sys.argv) == 1 else sys.argv[1:]

    failures = test_runner.run_tests(tests)
    if bool(failures):
        sys.exit(bool(failures))

    print("\n#######################################")
    print("  RUN TESTS WITH BOOLEAN FIELD ON ")
    print("#######################################\n")

    os.environ['DJANGO_SETTINGS_MODULE'] = 'safedelete.tests.settings_use_boolean_field'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    tests = ['safedelete.tests'] if len(sys.argv) == 1 else sys.argv[1:]
    failures = test_runner.run_tests(tests)
    sys.exit(bool(failures))
