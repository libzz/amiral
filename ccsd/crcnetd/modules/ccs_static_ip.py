# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# This file deals with static IP's
#
# Author:       Chris Browning <chris@rurallink.co.nz>
# Version:      $Id: ccs_graph.py 1434 2007-03-08 01:47:05Z ckb6 $
#
# crcnetd is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# crcnetd; if not, write to the Free Software Foundation, Inc., 
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC
ccs_mod_type = CCSD_SERVER

class ccs_static_pool_error(ccsd_error):
    pass


@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def addStaticIPPool(session_id, cidr, description):
    """ Create a static ip pool"""
    
    validateCIDR(cidr)
    session = getSessionE(session_id)
    
    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Created new static IP pool %s" % cidr, '', 1)
        commit = 1

    #Add entry to IP Pools
    sql = "INSERT INTO static_pools (pool_id, network, description) VALUES ( DEFAULT, %s, %s )"
    res = session.execute(sql, (cidr, description))

    # Get the pool_id that was created for the user
    sql = "SELECT currval('static_pools_pool_id_seq') AS pool_id"
    pool_id = session.query(sql, ())[0][0]


    num = ipnum(cidrToIP(cidr))
    count = pow(2,(32-cidrToLength(cidr)))

    #Loop through range, code below will remove "bad" addresses
    for i in range(num, num+count):
        naddr =  formatIP(i)
        part1,part2,part3,part4 = naddr.split('.')

        #Skip 0 and 255 even if they are in the middle of the range
        #for compatability with broken boxes (windows < XP, ...)
        if part4 in ['0','255']:
            continue
        
        #Add to db here
        sql = "INSERT INTO static_pool (ip_address, pool_id, login_id) VALUES ( %s, %s, NULL )"
        res = session.execute(sql, (naddr, pool_id))

    # If we started a changeset, commit it
    if commit == 1:
        session.commit()
    return 1

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getStaticIPPools(session_id):
    session = getSessionE(session_id)

    sql = "SELECT * from static_pools"
    return session.query(sql, ())
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getStaticIPPool(session_id, pool_id):
    session = getSessionE(session_id)

    sql = "SELECT p.ip_address, l.login_id, l.username, l.domain from static_pool p " \
        "LEFT JOIN logins l ON l.login_id = p.login_id WHERE pool_id = %s " \
        "ORDER BY p.ip_address"
    return session.query(sql, (pool_id))

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getStaticIPPoolStats(session_id):
    session = getSessionE(session_id)
    
    sql = "SELECT s.description, s.network, p.pool_id, coalesce(count(p.pool_id), 0) AS total, coalesce(ss.count, 0) " \
        "AS used FROM static_pool p JOIN static_pools s ON " \
        "s.pool_id = p.pool_id LEFT JOIN ( SELECT s.network, p.pool_id, " \
        "count(p.pool_id) FROM static_pool p JOIN static_pools s ON " \
        "s.pool_id = p.pool_id WHERE p.login_id IS NOT NULL GROUP BY s.network, p.pool_id) as ss ON " \
        "ss.pool_id = p.pool_id GROUP BY " \
        "s.network, p.pool_id, ss.count, s.description ORDER BY s.network"

    return session.query(sql, ())

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def freeStaticIPPool(session_id, pool_id):
    """ Unassign all used addresses in a pool """
    
    session = getSessionE(session_id)
    #Remove pool addresses
    sql = "UPDATE static_pool SET login_id = NULL WHERE pool_id = %s"
    res = session.execute(sql, (pool_id))
    return 1

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def delStaticIPPool(session_id, pool_id):
    """ Delete a static ip pool. This will fail if any 
    addresses are assigned """

    session = getSessionE(session_id)
    
    #Check whether there are any addresses from this pool in use
    count = session.getCountOf("SELECT count(*) as n FROM static_pool WHERE " \
            "pool_id=%s AND login_id IS NOT NULL", (pool_id))
    if count != 0:
        raise ccs_static_pool_error("%s address from the pool are still in " \
            "use" % count)

    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Removing static IP pool %s" % pool_id, '', 1)
        commit = 1

    #Remove pool addresses
    sql = "DELETE from static_pool WHERE pool_id = %s"
    res = session.execute(sql, (pool_id))

    #Remove entry from pools
    sql = "DELETE from static_pools WHERE pool_id = %s"
    res = session.execute(sql, (pool_id))

    # If we started a changeset, commit it
    if commit == 1:
        session.commit()
    return 1

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def unassignStaticIP(session_id, login_id):
    """ Unassosiate a login to a static address """

    session = getSessionE(session_id)

    #Update entry
    sql = "UPDATE static_pool SET login_id = NULL WHERE login_id = %s"
    res = session.execute(sql, (login_id))

    return 1

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def assignStaticIP(session_id, login_id, pool_id=None, address=None):
    """ Associate a login to a static ip address. If address is provided
    it will be used if valid, otherwise a free address will be assigned
    If the pool is suplied then an addresses from that pool only will
    be considered when doing allocations.
    
    Note if address is specified, pool_id is ignored.
    """

    session = getSessionE(session_id)
    
    cond = ""
    args = []
    
    # If not in a changeset, create one to group these commands together
    commit = 0
    if session.changeset == 0:
        session.begin("Assign Static IP", '', 1)
        commit = 1
    
    # Consider the pool selection
    if pool_id != None:
        cond = "AND pool_id = %s"
        args.append(pool_id)
    
    #If no address is supplied find a free one
    if address == None:
        #Find Free IP
        sql = "SELECT ip_address from static_pool where login_id IS NULL %s LIMIT 1;" % cond
        res = session.query(sql, args)

        if len(res) != 1:
            raise ccs_static_pool_error("No free addresses to allocate");
        else:
            address = res[0][0]

    #Check that supplied address can be used
    else:
        sql = "SELECT ip_address, login_id from static_pool where ip_address = %s;"
        res = session.query(sql, (address))

        if len(res) != 1:
            raise ccs_static_pool_error("Address %s not in pool" % address);

        res = res[0]
        if res[login_id] != "":
            raise ccs_static_pool_error("Address %s already assigned" % address);

    #Update entry
    sql = "UPDATE static_pool SET login_id = %s WHERE ip_address = %s"
    res = session.execute(sql, (login_id, address))

    # If we started a changeset, commit it
    if commit == 1:
        session.commit()

    return 1
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getStaticIP(session_id, login_id):
    session = getSessionE(session_id)

    sql = "SELECT ip_address from static_pool WHERE login_id = %s"
    res = session.query(sql, (login_id))

    if len(res) == 1:
        return res[0][0]
    else:
        return ""

def ccs_init():
    pass

