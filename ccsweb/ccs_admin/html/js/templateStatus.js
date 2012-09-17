/* Copyright (C) 2006  The University of Waikato
 *
 * This file is part of ccsweb - CRCnet Configuration System Web Interface 
 *
 * Author:       Matt Brown <matt@crc.net.nz>
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
Behaviour.addLoadEvent(initProgressBar);

function initProgressBar() {
    key = $F("statsKey");
    /* Handle initial load of an already in progress generation run */
    percent = $F("percent");
    updateProgressBar(percent);    
    if (percent != 100) {
        document.uploadStatus1 = new Ajax.PeriodicalUpdater('UploadStatus1',
            '/configs/status/' + key,
            Object.extend({asynchronous:true, evalScripts:true, 
            onComplete:stopProgressBar},{decay:1,frequency:1.0}));
        $('UploadStatus1').innerHTML='Initialising templates...';
    } else {
        // Viewing a historical generation run
        stopProgressBar();
    }
}
function updateProgressBar(to) {
    if ($('UploadProgressBar1')) {
        $('UploadProgressBar1').firstChild.firstChild.style.width= to +'%';
    }
}
function stopProgressBar() {
    if ($('UploadStatus1').innerHTML.indexOf("ERROR")!=-1) {
        Element.addClassName('UploadStatus1', 'error');
    }
    bar = $('UploadProgressBar1');
    if(bar){
        bar.firstChild.firstChild.className = "finished";
    };
    document.uploadStatus1 = null;
}
