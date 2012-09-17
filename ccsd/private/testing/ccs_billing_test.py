#!/usr/bin/python
# This file contains testing for ccs_billing. 
#
# XXX: Add better output.
# XXX: Add api more like unit testing.

import xmlrpclib
import httplib
import sys

class MyTransport(xmlrpclib.Transport):
    def _init_(self,key, cert):
        self._key = key
        self._cert = cert
        return self

    def make_connection(self, host):
        """Overrides the standard make_connection method
        Specifies client certificates for the connection
        """
        
        host, extra_headers, x509 = self.get_host_info(host)
        try:
            HTTPS = httplib.HTTPS
        except AttributeError:
            raise NotImplementedError(
                "your version of httplib doesn't support HTTPS"
            )
        else:
            return HTTPS(host, None, key_file=self._key, cert_file=self._cert);

def usage():
    print "Usage: %s server:port key cert" % (sys.argv[0])

def addGenericPlan(rpc):
    details = {}
    details["plan_name"] = "ccs_testddd_plan"
    details["description"] = "This dddis a test"
    details["price"] = 11.11
    details["radius_plan"] = 1 
    details["included_mb"] = 334
    details["cap_period"] = "daily"
    details["cap_action"] = "purchase"
    details["cap_param"] = 5
    details["cap_price"] = 4

    return rpc.addPlan({}, details)[0]["plan_id"]
    

def testAddPlan(rpc):
    """
    Adds a plan and then retrieves it and checks that all the fields are ok.
    """
    print "Starting add plan test."
    details = {}
    details["plan_name"] = "ccs_test_plan"
    details["description"] = "This is a test"
    details["price"] = 77.77
    details["radius_plan"] = 1 
    details["included_mb"] = 1024
    details["cap_period"] = "weekly"
    details["cap_action"] = "throttle"
    details["cap_param"] = 1
    details["cap_price"] = 0
    
    res = rpc.addPlan({},details)
    
    res = rpc.getPlan({},res[0]["plan_id"])
    for keys in details:
        if details[keys] != res[0][keys]:
            print "Failed on key '%s'.\n" % (keys)
            return False

    print "Add plan test completed succesfully\n"


def testEditPlan(rpc):
    """
    Adds a plan. Retrieves it, edits it, and thhen tests
    to see if its been edited ok.
    """
    print "Starting edit plan test."
    details = {}
    details["plan_name"] = "ccs_test_edit_plan"
    details["description"] = "This is a test srsly"
    details["price"] = 66.66
    details["radius_plan"] = 1 
    details["included_mb"] = 2048
    details["cap_period"] = "monthly"
    details["cap_action"] = "purchase"
    details["cap_param"] = 0
    details["cap_price"] = 44.44
    details["plan_id"] = addGenericPlan(rpc)
    rpc.editPlan({}, details)
    res = rpc.getPlan({}, details["plan_id"])
    for keys in details:
        if res[0][keys] != details[keys]:
            print "Edit Plan test failed at key: %s\n" % (keys)
            return False
    
    
    print "Edit plan test passed.\n"
    return True

def testRemovePlan(rpc):
    print "Starting remove plan test."
    plan_id = addGenericPlan(rpc)

    rpc.removePlan({}, plan_id)

    res = rpc.getPlan({}, plan_id)

    if len(res) != 0:
        print "Failed remove plan test.\n"
        return False
    
    print "Remove plan test passed.\n"
    return True

def testAddCustomer(rpc):
    print "Add Customer test started."
    details = {}
    details["username"] = "testername"
    details["givenname"] = "tester"
    details["surname"] = "tester"
    details["phone"] = "+64 7 853 2070"
    details["email"] = "john@ivan.net.nz"
    details["type"] = "customer"
    details["address"] = "asassa"
    details["enabled"] = 1
    details["plan_id"] = 1
    details["billing_name"] = "billingname"
    details["billing_address"] = "aaaaaa"

    contact_id = rpc.addCustomer({}, details)
    res = rpc.getCustomer({}, contact_id)
    
    for keys in details:
        if details[keys] != res[0][keys]:
            print "Add Customer test failed.\n"
            return False

    rpc.delContact({}, contact_id)
    print "Add Customer test passed.\n"
    return True

def testEditCustomer(rpc):
    print "Edit Customer test starting."
    res = rpc.getCustomerList({})
    
    details = {}
    details["username"] = res[0]["username"]
    details["contact_id"] = res[0]["contact_id"]
    details["givenname"] = "tester"
    details["surname"] = "tester"
    details["phone"] = "+64 7 853 2070"
    details["email"] = "john@ivan.net.nz"
    details["type"] = "customer"
    details["address"] = "asassa"
    details["enabled"] = 1
    details["plan_id"] = 1
    details["billing_name"] = "billingname"
    details["billing_address"] = "aaaaaa"
    
    rpc.editCustomer({}, details)
    
    res = rpc.getCustomer({}, details["contact_id"])
    for keys in details:
        if details[keys] != res[0][keys]:
            print "Edit Customer test failed.\n"
            return False

    print "Edit Customer test passed.\n"

#### Main program ####
if len(sys.argv) != 4:
    usage()
    sys.exit(-1)

s = xmlrpclib.ServerProxy("https://%s/RPC2" % (sys.argv[1]), \
    MyTransport()._init_(sys.argv[2], sys.argv[3]))

testAddPlan(s)
testEditPlan(s)
testRemovePlan(s)
testAddCustomer(s)
testEditCustomer(s)

