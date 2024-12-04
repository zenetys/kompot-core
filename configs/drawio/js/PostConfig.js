/**
 * Copyright (c) 2006-2024, JGraph Ltd
 * Copyright (c) 2006-2024, draw.io AG
 */
// null'ing of global vars need to be after init.js
window.VSD_CONVERT_URL = null;
window.EMF_CONVERT_URL = null;
window.ICONSEARCH_PATH = null;

window.App.pluginRegistry.live = 'js/live.js';

(function () {
    function forceRegisterPluginViaUrlParams(id) {
        plist = typeof urlParams.p === 'string' && urlParams.p.length > 0
            ? urlParams.p.split(';') : [];
        if (plist.indexOf(id) == -1)
            plist.push(id);
        urlParams.p = plist.join(';');
    }

    forceRegisterPluginViaUrlParams('live');
})();
