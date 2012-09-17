/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface
 *
 * Functions for billing
 * 
 * Author:       Ivan Meredith <ivan@ivan.net.nz
 * Version:      $Id$
 *
 * ccsweb is free software; you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation.
 *
 * ccsweb is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * ccsweb; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

var myrules = {
    '#num' : function(element){
        element.onchange = num_disp_results;
    },
    '#reset' : function(element){
        element.onclick = reset_search;
    },
};

Behaviour.register(myrules);

function reset_search()
{
    window.location="/mods/billing";
}
function num_disp_results()
{
    document.forms['searchform'].submit();
}
