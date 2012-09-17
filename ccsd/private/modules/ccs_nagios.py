# Copyright (C) 2006  The University of Waikato
#
# Nagios Service Module for the CRCnet Configuration System
# Configures nagios to monitor the network
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
#
from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC
from crcnetd._utils.ccsd_service import ccsd_service, ccs_service_error, \
        registerService

from crcnetd.modules.ccs_contact import addGroup, getGroupID, getUsers, \
        isGroupMemberU, getGroup, getMembers

ccs_mod_type = CCSD_SERVER

NAGIOS_GROUP_NAME = "Nagios Contacts"

class nagios_error(ccs_service_error):
    pass

class nagios_service(ccsd_service):
    """Configures the nagios service on a host"""
    
    serviceName = "nagios"
    allowNewProperties = True
    networkService = True

    def __init__(self, session_id, service_id):
        # Call base class setup
        ccsd_service.__init__(self, session_id, service_id)

    @exportViaXMLRPC(SESSION_RO, AUTH_ADMINISTRATOR, True, \
            "getHostNagiosDetails")
    def getHostDetails(self, host_id):
        """Returns data relating to nagios on a host"""
        session = getSessionE(self._session_id)

        service = ccsd_service.getHostDetails(self, host_id)

        return service

    def getContacts(self):
        """Returns a list of contacts that can receive nagios notifications

        This includes anyone in the Administrators group and also anyone in a
        group that is a member of the Nagios Contacts group.
        """
        contacts = {}
        admin_group = getGroupID(self._session_id, AUTH_ADMINISTRATOR)
        nagios_group = getGroupID(self._session_id, NAGIOS_GROUP_NAME)

        # Get a list of all contacts
        all_contacts = getUsers(self._session_id)
        
        # Check whether each contact is in the necessary group
        for contact in all_contacts:
            # For now assume all contacts want all notifications
            # XXX: Must fix
            contact["notify_none"] = False
            contact["notify_service_critical"] = True
            contact["notify_service_warning"] = True
            contact["notify_service_unknown"] = True
            contact["notify_service_recovery"] = True
            contact["notify_host_down"] = True
            contact["notify_host_unreachable"] = True
            contact["notify_host_recovery"] = True
            # Check if they are an administrator
            if admin_group != -1:
                if isGroupMemberU(self._session_id, contact["admin_id"], \
                        admin_group, False):
                    contacts[contact["username"]] = contact
                    continue
            # Check if they are in the nagios group
            if nagios_group != -1:
                if isGroupMemberU(self._session_id, contact["admin_id"], \
                        nagios_group, False):
                    contacts[contact["username"]] = contact
                    continue
        
        return contacts
    
    def membersList(self, group_id):
        """Returns a list of usernames that are members of the group"""
        members = []
        
        for member in getMembers(self._session_id, group_id):
            members.append(member["username"])
    
        return members
    
    def getContactGroups(self):
        """Returns a list of contact groups that can receive notifications

        This consists of the Administrators group and group that is a member
        of the Nagios Contacts group.
        """

        groups = {}
        admin_group = getGroupID(self._session_id, AUTH_ADMINISTRATOR)
        nagios_group = getGroupID(self._session_id, NAGIOS_GROUP_NAME)

        if admin_group != -1:
            admins = getGroup(self._session_id, admin_group)
            admins["members"] = self.membersList(admin_group)
            groups[AUTH_ADMINISTRATOR] = admins

        # Loop through the members of the nagios group
        if nagios_group != -1:
            for member in getMembers(self._session_id, nagios_group):
                group_id = member["group_id"]
                if group_id == "" or group_id is None:
                    continue
                group = getGroup(self._session_id, group_id)
                group["members"] = self.membersList(group_id)
                groups[group["group_name"]] = group
                
        return groups
    
    def getNetworkTemplateVariables(self):
        """Returns a dictionary containing template variables for a host

        See the getTemplateVariables function for more details.
        """
        md5_key = ""

        # Call base class to get the basics
        variables = ccsd_service.getNetworkTemplateVariables(self)

        variables["contacts"] = self.getContacts()
        variables["contact_groups"] = self.getContactGroups()
        variables["default_contact_group"] = AUTH_ADMINISTRATOR
        variables["host_classes"] = {}
        variables["parents"] = {}
        variables["generateNagiosHostList"] = generateNagiosHostList

        return variables
    
    @staticmethod
    def initialiseService():
        """Called by the system the very first time the service is loaded.

        This should setup an entry in the service table and load any default
        service properties into the service_prop table.
        """
        session = getSessionE(ADMIN_SESSION_ID)
        session.begin("initialising Nagios service")        
        try:

            session.execute("INSERT INTO service (service_id, service_name, " \
                    "enabled) VALUES (DEFAULT, %s, DEFAULT)", \
                    (nagios_service.serviceName))
            service_id = session.getCountOf("SELECT currval('" \
                    "service_service_id_seq') AS server_id", ())

            # Create the Nagios Contacts group if it doesn't exist
            try:
                id = getGroupID(session.session_id, NAGIOS_GROUP_NAME)
                if id==-1:
                    addGroup(session.session_id, \
                            {"group_name":NAGIOS_GROUP_NAME})
            except:
                log_error("Could not initialise the Nagios group!", \
                        sys.exc_info())
                
            # Commit the changese
            session.commit()
            
            log_info("Created nagios service entries and tables in database")
        except:
            session.rollback()
            log_error("Unable to initialise nagios database entries!", \
                    sys.exc_info())
            raise nagios_error("Failed to setup database tables!")

        return service_id
    
def generateNagiosHostList(hosts):
    
    if type(hosts) == type({}):
        hosts = hosts.values()

    hostlist = ""
    for host in hosts:
        if type(host) == type({}):
            if not host["host_active"]:
                continue
            name = host["host_name"]
        else:
            name = host
        if hostlist != "": hostlist += ","
        hostlist += name

    return hostlist

def ccs_init():
    registerService(nagios_service)
