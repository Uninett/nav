// Extended Tooltip Javascript
// copyright 9th August 2002, by Stephen Chapman, Felgall Pty Ltd

// permission is granted to use this javascript provided that the below code is not altered
var DH = 0;var an = 0;var al = 0;var ai = 0;if (document.getElementById) {ai = 1; DH = 1;}else {if (document.all) {al = 1; DH = 1;} else { browserVersion = parseInt(navigator.appVersion); if ((navigator.appName.indexOf('Netscape') != -1) && (browserVersion == 4)) {an = 1; DH = 1;}}} function fd(oi,ws) {if (ws == 1) {if (ai) {return (document.getElementById(oi).style);}
else {if (al) {return (document.all[oi].style);} else {if (an) {return (document.layers[oi]);}};}} else {if (ai) {return (document.getElementById(oi));} else {if (al) {return (document.all[oi]);} else {if (an) {return (document.layers[oi]);}};}}} function pw() {if (window.innerWidth != null) return window.innerWidth; if (document.body.clientWidth != null)
return document.body.clientWidth; return (null);} function popUp(evt,oi) {if (DH) {var wp = pw(); ds = fd(oi,1); dm = fd(oi,0); st = ds.visibility; if (dm.offsetWidth) ew = dm.offsetWidth; else if (dm.clip.width) ew = dm.clip.width; if (st == "visible" || st == "show") { ds.visibility = "hidden"; } else  { if (evt.y || evt.pageY) {if (evt.pageY) {tv = evt.pageY + 20;
lv = evt.pageX - (ew/4);} else {tv = evt.y + 20 + document.body.scrollTop; lv = evt.x  - (ew/4) + document.body.scrollLeft;} if (lv < 2) lv = 2; else if (lv + ew > wp) lv -= ew/2; ds.left = lv; ds.top = tv;} ds.visibility = "visible";}}}
