-- Copyright (C) 2006  The University of Waikato
--
-- Base Data for the Waikato CRCnet Network
--
-- Author:   Matt Brown  <matt@crc.net.nz>
-- Version:  $Id: crcnetbase.sql 446 2005-11-10 20:38:39Z mglb1 $
--
-- No usage or redistribution rights are granted for this file unless
-- otherwise confirmed in writing by the copyright holder.
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
INSERT INTO changeset VALUES (DEFAULT, NOW(), 'admin', 'Base data for the Waikato CRCnet Network',
    NULL, 't');

INSERT INTO kernel VALUES (1, 'default', '', 1, '2005-08-30');

INSERT INTO link_class VALUES (DEFAULT, 'Internal Networks', '10.1.0.0/17', 24, 't');
INSERT INTO link_class VALUES (DEFAULT, 'Routing Networks', '10.1.128.0/17', 24, 'f');
INSERT INTO link_class VALUES (DEFAULT, 'Loopback Addresses', '10.1.128.0/24', 32, 't');


INSERT INTO link VALUES (DEFAULT, 'University Transit', 'Ethernet', '100', 1,
    NULL, NULL, NULL, '10.1.250.0/24', 'f');
INSERT INTO link VALUES (DEFAULT, 'MSB AP A', 'Managed', 'b', 1,
    'CRCnet-msb-a', 1, NULL, '10.1.221.0/24', 'f');
INSERT INTO link VALUES (DEFAULT, 'MSB AP B', 'Managed', 'b', 1,
    'CRCnet-msb-b', 11, NULL, '10.1.220.0/24', 'f');

INSERT INTO contact VALUES (DEFAULT, 'Brown', 'Matt', '+64 275 611 544', 
    'matt@crc.net.nz', 'matt', nextval('uid_seq'), '', 
    '$1$4jDDUiqO$zwT5Tb5sDrIQpD3g705P4.', '', '', 1, 'normal', NOW());
--INSERT INTO contact VALUES (DEFAULT, 'Curtis', 'Jamie', '+64 21 392 102',
--    'jamie@wand.net.nz', 'jpc2', nextval('uid_seq'), '',
--    '$1$4jDDUiqO$zwT5Tb5sDrIQpD3g705P4.', '', '', 1, 'normal', NOW());
INSERT INTO group_membership (parent_group_id, contact_id) VALUES (1, 1);
--INSERT INTO group_membership (parent_group_id, contact_id) VALUES (1, 2);

INSERT INTO module VALUES (DEFAULT, 'orinoco_cs', 'f', 't', 'f', 'f');
INSERT INTO module VALUES (DEFAULT, 'hostap', 't', 't', 'f', 'f');
INSERT INTO module VALUES (DEFAULT, 'hostap_cs', 't', 't', 'f', 'f');
INSERT INTO module VALUES (DEFAULT, 'madwifi', 't', 't', 't', 't');

INSERT INTO site VALUES (DEFAULT, 0, 0, 0, 'Scrapped Stock', 1, 1, '');
INSERT INTO site VALUES (DEFAULT, 0, 0, 0, 'Stock on Loan', 1, 1, '');
INSERT INTO site VALUES (DEFAULT, 0, 0, 0, 'Stock (RSC)', 1, 1, '');
INSERT INTO site VALUES (DEFAULT, 0, 0, 0, 'Stock (G Block)', 1, 1, '');
INSERT INTO asset_stock_location VALUES (DEFAULT, 3, 't');
INSERT INTO asset_stock_location VALUES (DEFAULT, 4, 'f');

INSERT INTO asset_type VALUES (DEFAULT, 'Soekris net4521');
INSERT INTO asset_type VALUES (DEFAULT, 'Soekris net4511');
INSERT INTO asset_type VALUES (DEFAULT, 'Soekris net4526');
INSERT INTO asset_type VALUES (DEFAULT, 'Soekris net4826');
--INSERT INTO asset_type VALUES (DEFAULT, 'Advantech Biscuit PC');
--INSERT INTO asset_type VALUES (DEFAULT, 'Computers');
INSERT INTO asset_type VALUES (DEFAULT, 'Hermes 802.11b Card');
INSERT INTO asset_type VALUES (DEFAULT, 'Prism2 802.11b miniPCI Card');
INSERT INTO asset_type VALUES (DEFAULT, 'Prism2 802.11b PCMCIA Card');
INSERT INTO asset_type VALUES (DEFAULT, 'Atheros 802.11abg miniPCI Card');
--INSERT INTO asset_type VALUES (DEFAULT, 'Equipment');
--INSERT INTO asset_type VALUES (DEFAULT, 'PCMCIA Bridge Cards');
--INSERT INTO asset_type VALUES (DEFAULT, 'Videoconference Units');
--INSERT INTO asset_type VALUES (DEFAULT, 'UPS Units');
--INSERT INTO asset_type VALUES (DEFAULT, 'Antenna');
--INSERT INTO asset_type VALUES (DEFAULT, 'Access Point / Bridging Devices');

INSERT INTO asset_type_map VALUES ('host', 1);
INSERT INTO asset_type_map VALUES ('host', 2);
INSERT INTO asset_type_map VALUES ('host', 3);
INSERT INTO asset_type_map VALUES ('host', 4);
--INSERT INTO asset_type_map VALUES ('host', 5);
--INSERT INTO asset_type_map VALUES ('host', 6);
INSERT INTO asset_type_map VALUES ('interface', 5);
INSERT INTO asset_type_map VALUES ('interface', 6);
INSERT INTO asset_type_map VALUES ('interface', 7);
INSERT INTO asset_type_map VALUES ('interface', 8);

INSERT INTO module_map VALUES (DEFAULT, 1, 5, 't');
INSERT INTO module_map VALUES (DEFAULT, 2, 6, 't');
INSERT INTO module_map VALUES (DEFAULT, 3, 5, 't');
INSERT INTO module_map VALUES (DEFAULT, 3, 7, 't');
INSERT INTO module_map VALUES (DEFAULT, 4, 8, 't');

INSERT INTO subasset_type VALUES (DEFAULT, 'Ethernet Interface');
INSERT INTO subasset_type VALUES (DEFAULT, 'Wireless Interface');
INSERT INTO subasset_type VALUES (DEFAULT, 'Wireless Interface (VAP Interface)');
INSERT INTO subasset_type VALUES (DEFAULT, 'Motherboard');
INSERT INTO subasset_type_map VALUES ('interface', 1);
INSERT INTO subasset_type_map VALUES ('interface', 2);
INSERT INTO subasset_type_map VALUES ('wireless_interface', 2);
INSERT INTO subasset_type_map VALUES ('interface', 3);
INSERT INTO subasset_type_map VALUES ('wireless_interface', 3);
INSERT INTO subasset_type_map VALUES ('vap', 3);

INSERT INTO asset_type_subasset VALUES (DEFAULT, 1, 1, 'eth0', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 1, 1, 'eth1', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 1, 4, 'Soekris net4521', true);

INSERT INTO asset_type_subasset VALUES (DEFAULT, 2, 1, 'eth0', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 2, 1, 'eth1', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 2, 4, 'Soekris net4511', true);

INSERT INTO asset_type_subasset VALUES (DEFAULT, 3, 1, 'eth0', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 3, 4, 'Soekris net4526', true);

INSERT INTO asset_type_subasset VALUES (DEFAULT, 4, 1, 'eth0', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 4, 4, 'Soekris net4826', true);

--INSERT INTO asset_type_subasset VALUES (DEFAULT, 5, 1, 'eth0', true);
--INSERT INTO asset_type_subasset VALUES (DEFAULT, 5, 1, 'eth1', true);
--INSERT INTO asset_type_subasset VALUES (DEFAULT, 5, 3, 'Advantech', true);

--INSERT INTO asset_type_subasset VALUES (DEFAULT, 6, 1, 'eth0', false);
--INSERT INTO asset_type_subasset VALUES (DEFAULT, 6, 3, 'Motherboard', true);

INSERT INTO asset_type_subasset VALUES (DEFAULT, 5, 2, 'wireless', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 6, 2, 'wireless', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 7, 2, 'wireless', true);
INSERT INTO asset_type_subasset VALUES (DEFAULT, 8, 3, 'wireless', true);

--INSERT INTO asset_type_subasset VALUES (DEFAULT, 16, 1, 'wired', false);
--INSERT INTO asset_type_subasset VALUES (DEFAULT, 16, 2, 'wireless', false);

INSERT INTO asset_property VALUES (DEFAULT, 'MAC Address');
INSERT INTO asset_property VALUES (DEFAULT, 'Storage (CF/HDD) (MB)');
INSERT INTO asset_property VALUES (DEFAULT, 'RAM (MB)');
INSERT INTO asset_property VALUES (DEFAULT, 'Processor Class');
INSERT INTO asset_property VALUES (DEFAULT, 'Processor (Mhz)');

INSERT INTO subasset_property VALUES (DEFAULT, 1, 1, 't', NULL);
INSERT INTO subasset_property VALUES (DEFAULT, 2, 1, 't', NULL);
INSERT INTO subasset_property VALUES (DEFAULT, 3, 2, 't', '64');
INSERT INTO subasset_property VALUES (DEFAULT, 3, 3, 't', '64');
INSERT INTO subasset_property VALUES (DEFAULT, 3, 4, 't', '486');
INSERT INTO subasset_property VALUES (DEFAULT, 3, 5, 't', '133');

UPDATE changeset SET pending='f' WHERE pending='t' AND username='admin';
COMMIT;
