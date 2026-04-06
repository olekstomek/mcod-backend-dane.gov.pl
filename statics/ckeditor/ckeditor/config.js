/**
 * @license Copyright (c) 2003-2022, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here. For example:
	// config.language = 'fr';
	// config.uiColor = '#AADC6E';
    config.removePlugins = 'easyimage, cloudservices, exportpdf';

CKEDITOR.on('dialogDefinition', function(ev) {
    var dialogName = ev.data.name;
    var dialogDefinition = ev.data.definition;

    if (dialogName == 'image') {
        var infoTab = dialogDefinition.getContents('info');

        // Get the URL text field
        var urlField = infoTab.get('txtUrl');

        // Option A: Hide it completely (User must use the Upload tab)
        urlField.hidden = true;

    }
});


};
