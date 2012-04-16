# -*- coding: utf-8 -*-
from nav.tests.cases import ModPythonTestCase
from nav.models.profiles import Account, Organization, Location, Room
from django.db import transaction
from StringIO import StringIO

from nav.web.report import handler

class ReportEncodingTest(ModPythonTestCase):
    module_under_test = handler

    def setUp(self):
        super(ReportEncodingTest, self).setUp()

        transaction.enter_transaction_management()
        transaction.managed(True)
        admin = Account.objects.get(login='admin')
        admin.name = u"ÆØÅ Test Administrator"
        admin.save()

        org = Organization(id=u"møøse", description=u"møøse biting unit")
        org.save()

        loc = Location(id=u"sømewhere", description="øver the rainbøw")
        loc.save()

        room = Room(id=u"æøå", description="The Norwegian blue room",
                    location=loc)
        room.save()


    def tearDown(self):
        super(ReportEncodingTest, self).tearDown()

        transaction.rollback()
        transaction.leave_transaction_management()

    def test_index_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/")

    def test_matrix_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/matrix")

    def test_reportlist_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/reportlist")

    def test_netbox_report_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/netbox")

    def test_org_report_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/org")

    def test_location_report_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/location")

    def test_room_report_no_unicode_output(self):
        self.handler_outputs_no_unicode("/report/room")

    def test_admin_name_present_in_output(self):
        buffer = StringIO()
        admin_substring = '\xc3\x86\xc3\x98\xc3\x85'
        request = self.make_request("/report/")
        request.write = buffer.write

        self.assertEquals(handler.handler(request), 200)

        buffer.seek(0)
        output = buffer.read()
        self.assertTrue(admin_substring in output,
                        "%r not in %r" % (admin_substring, output))

