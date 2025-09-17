odoo.define('easy_jsonapi.documentation', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var JsonapiDoc = AbstractAction.extend({
        template: 'JsonapiDocumentations',
    });
    core.action_registry.add('json_api_doc', JsonapiDoc);
    return JsonapiDoc;
});