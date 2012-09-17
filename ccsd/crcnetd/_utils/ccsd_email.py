# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# This file contains common code used to process emails
# 
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
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
import smtplib
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

#############################################################################
# Helper Functions
#############################################################################
def send_mail(send_from, send_to, subject, text, files=[], cc=[], bcc=[]):
    """Send an email, optionally with some attachments"""
    from ccsd_config import config_get

    # Try and read the server and domain from the config file, but this 
    # might fail, if it hasn't been started yet
    try:
        server = config_get("network", "smtp_server", "localhost")
    except:
        server = "localhost"
    try:
        domain = config_get("network", "domain")
    except:
        domain = "localhost"

    # Ensure the sender address is fully qualified
    if send_from.find("@") == -1:
        send_from = "%s@%s" % (send_from, domain)

    # Create the MIME message
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    # Handle Carbon-copy recipients
    if len(cc) > 0:
        msg['CC'] = COMMAPSACE.join(cc)
        send_to.extend(cc)

    # Handle Blind-carbon-copy recipients
    if len(bcc) > 0:
        send_to.extend(bcc)

    # Attach the message text
    msg.attach( MIMEText(text) )

    # Attach files
    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 
                'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    # Send the message
    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
    return True
