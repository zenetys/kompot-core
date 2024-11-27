/**
 * Copyright (c) 2006-2024, JGraph Ltd
 * Copyright (c) 2006-2024, draw.io AG
 */
// Overrides of global vars need to be pre-loaded
window.DRAWIO_PUBLIC_BUILD = true;
window.EXPORT_URL = 'REPLACE_WITH_YOUR_IMAGE_SERVER';
window.PLANT_URL = 'REPLACE_WITH_YOUR_PLANTUML_SERVER';
window.DRAWIO_BASE_URL = null; // Replace with path to base of deployment, e.g. https://www.example.com/folder
window.DRAWIO_VIEWER_URL = null; // Replace your path to the viewer js, e.g. https://www.example.com/js/viewer.min.js
window.DRAWIO_LIGHTBOX_URL = null; // Replace with your lightbox URL, eg. https://www.example.com
window.DRAW_MATH_URL = 'math/es5';
window.DRAWIO_CONFIG = null; // Replace with your custom draw.io configurations. For more details, https://www.drawio.com/doc/faq/configure-diagram-editor

window.mxLanguageMap = {
    i18n: '',
    en: 'English',
    fr: 'Français',
};

urlParams['sync'] = 'manual';
// urlParams['lang'] = 'fr';
// urlParams['ui'] = 'min';
urlParams['draft'] = 0;
urlParams['splash'] = 0;
urlParams['picker'] = 1;
urlParams['thumb'] = 0;
urlParams['edge'] = 'move';
urlParams['rt'] = 0;
urlParams['save'] = 'local';
urlParams['gapi'] = 0;
urlParams['db'] = 0;
urlParams['od'] = 0;
urlParams['tr'] = 0;
urlParams['gh'] = 0;
urlParams['gl'] = 0;
urlParams['drive'] = 0;
urlParams['mode'] = 'browser';
// urlParams['offline'] = 1;
urlParams['pwa'] = 0;

function cState2(h,s) {
  let sha=[0,2,4,0,7,0,0,0,9,0,0,0,0,0,0,0,0];
  let ssa=[0,1,3,0,5,0,0,0,8,0,0,0,0,0,0,0,6];
  let st=sha[h.status];
  for([k,v] of Object.entries(s)) st=ssa[v.status]>st?ssa[v.status]:st;;
  return(st<=2?"grey":st<=4?"green":st<=5?"yellow":st<=7?"red":"orange");
}

function cState(d) {
  const GREEN = "#4CAF50";
  const ORANGE = "#F57C00";
  const RED = "#E53935";
  const GREY = "#A0A0A0";
  const BLUE = "#80D8FF";
  const st = {
    0:GREY,
    1:GREY,
    2:GREY,
    3:GREEN,
    4:GREEN,
    5:ORANGE,
    6:ORANGE,
    7:ORANGE,
    8:RED,
    9:RED,
  };
  if (typeof(d) === "undefined")
    return GREY;
  return (st[d.state]);
}

function cName(d) {
  if (typeof(d) === "undefined")
    return "UNDEFINED";
  return (d.name);
}

function outputDiv(text, width, height) {
  if (typeof(text) === "undefined")
    return "UNDEFINED";
  return "<div style=\"overflow:scroll;width:"+width+";height:"+height+";\">"+text+"</div>";
}

function htmlEntities(s) {
  const entities = { "&":"&amp", "<":"&lt;", ">":"&gt;", '"':"&quot;",
                     "'":"&apos;" };
  return (s.replace(/([&<>\"'])/g, m => entities[m]));
}

function color(status) {
  let sha=[0,2,4,0,7,0,0,0,9,0,0,0,0,0,0,0,0];
  let ssa=[0,1,3,0,5,0,0,0,8,0,0,0,0,0,0,0,6];
  let st=ssa[status];
  return(st<=2?"grey":st<=4?"green":st<=5?"yellow":st<=7?"red":"orange");
}

function state2color(status) {
  return(status==0?"green":status==1?"yellow":status==2?"red":"orange");
}
