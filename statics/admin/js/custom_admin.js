/* jshint esversion: 6 */

document.addEventListener('DOMContentLoaded', function () {
    "use strict";

    // ================================================================
    // 1. Obsługa menu użytkownika (Show/Hide User List)
    // ================================================================
        const triggerContainer = document.getElementById("user-gov-list-container");
        if (triggerContainer) {
            triggerContainer.addEventListener('click', toggleUserList);
        }

    function toggleUserList() {
        const userList = document.getElementById("user-gov-list");
        const image = document.getElementById("switch-image");

        if (!userList || !image) return;

        // Obrót strzałki
        if (image.classList.contains("rotate")) {
            image.classList.remove("rotate");
        } else {
            image.classList.add("rotate");
        }

        // Pokazywanie/ukrywanie listy
        if (userList.style.display === "flex") {
            userList.style.display = "none";
        } else {
            userList.style.display = "flex";
            userList.style.flexDirection = "column";
        }
    }

    // ================================================================
    // 2. Obsługa dynamicznych widgetów
    // ================================================================
    if (typeof django !== 'undefined' && django.jQuery) {
        (function ($) {

            // --- A. Obsługa paginacji "Pokaż wszystko" (z pagination.html) ---
            // Zachowuje "kotwicę" (hash) w adresie URL po kliknięciu linku
            $("a.showall").off('click').on('click', function () {
                const anchor = window.location.hash;
                if (anchor) {
                    const currentHref = $(this).attr('href');
                    if (currentHref.indexOf(anchor) === -1) {
                        $(this).attr('href', currentHref + anchor);
                    }
                }
            });
        })(django.jQuery);
    }

    // ================================================================
    // 3. Obsługa filtra ról (Multiselect) - User Change List
    // ================================================================
    const $jq = window.jQuery || window.Suit.$;
    if ($jq && $jq.fn.multiselect) {
        $jq(() => {
            const $roleFilter = $jq('#user-roles-filter');
            if ($roleFilter.length) {
                $roleFilter.attr('name', 'role');
                const placeholderText = $roleFilter.data('non-selected-text') || "Wybierz rolę";

                $roleFilter.multiselect({
                    nonSelectedText: placeholderText, numberDisplayed: 6,
                    templates: {
                        li: '<li><a href="#" tabindex="0"><label></label></a></li>'
                    },
                    onChange: (option, checked) => {
                        const value = $jq(option).val();
                        const $targetOption = $jq(`#user-roles-filter option[value="${value}"]`);
                        $targetOption.prop('selected', checked);
                        if (checked) {
                            $targetOption.attr('selected', 'selected');
                        } else {
                            $targetOption.removeAttr('selected');
                        }
                    }
                });
            }
        });
    }

    // ================================================================
    // 4. Obsługa DateFilter (ładowanie widgetów kalendarza)
    // ================================================================
    if (typeof django !== 'undefined' && django.jQuery) {
        (function ($) {
            function getNonce() { var script = document.querySelector('script[nonce]'); return script ? script.nonce : ''; }
            function loadScriptWithNonce(url) {
                const dfd = $.Deferred();
                const script = document.createElement('script');
                script.src = url; script.nonce = getNonce();
                script.onload = function () { dfd.resolve(); };
                script.onerror = function () { dfd.reject(); };
                document.head.appendChild(script);
                return dfd.promise();
            }

            const $dateFilter = $('.admindatefilter');
            if ($dateFilter.length && !('DateTimeShortcuts' in window)) {
                const scriptsToLoad = $dateFilter.data('required-scripts');
                if (Array.isArray(scriptsToLoad) && scriptsToLoad.length > 0) {
                    const scriptPromises = scriptsToLoad.map(function (scriptUrl) {
                        return loadScriptWithNonce(scriptUrl);
                    });
                    const finalDeferred = $.Deferred(function (deferred) { $(deferred.resolve); });
                    scriptPromises.push(finalDeferred);
                    $.when.apply($, scriptPromises).done(function () {
                        $('.datetimeshortcuts').remove();
                        if ('DateTimeShortcuts' in window) {
                            DateTimeShortcuts.init();
                        }
                    });
                }
            }
        })(django.jQuery);
    }

    // ================================================================
    // 5. External Datasets Widget (Moved from external_datasets.html)
    // ================================================================
    if (typeof django !== 'undefined' && django.jQuery) {
        (function ($) {
            $(document).ready(function () {
                const $widgetContainer = $('.external-datasets-widget');
                if ($widgetContainer.length) {
                    $widgetContainer.each(function () {
                        const $container = $(this);
                        const iconUrl = $container.data('icon-url');
                        const altText = $container.data('alt-text');
                        const namePlaceholder = $container.data('name-placeholder');
                        const linkPlaceholder = $container.data('link-placeholder');
                        const buttonHtml = `<button type="button" class="add-related customfields add-customfield-btn"><img src="${iconUrl}" alt="${altText}"></button>`;
                        const pairHtml = `<br><input type="text" name="json_key[customfields]" value="" placeholder="${namePlaceholder}"><input type="url" name="json_value[customfields]" value="" placeholder="${linkPlaceholder}" size="35" class="customfields">`;

                    // Wstaw przycisk "Dodaj" za ostatnim polem linku w tym kontenerze
                    // Jeśli lista jest pusta (brak items_list), appendujemy do kontenera
                        const $lastField = $container.find('.customfields').last();
                        if ($lastField.length) { $lastField.after(buttonHtml); } else { $container.append(buttonHtml); }
                        $container.on('click', '.add-customfield-btn', function () { $(this).before(pairHtml); });
                    });
                }
            });
        })(django.jQuery);
    }

    // ================================================================
    // 6. Global Autosize Textarea (Native JS Implementation)
    // ================================================================
    {
        const $jq = window.Suit ? window.Suit.$ : (window.jQuery || (typeof django !== 'undefined' ? django.jQuery : null));
        if ($jq) {
            $jq(document).ready(function() {

                // Funkcja wykonująca zmianę wysokości
                function adjustHeight(el) {
                    el.style.height = 'auto';
                    el.style.height = (el.scrollHeight + 2) + 'px';
                }

                // Funkcja inicjująca dla grupy elementów
                function initAutosize(elements) {
                    elements.each(function() {
                        var el = this;
                        el.style.overflowY = 'hidden'; el.style.resize = 'none';
                        adjustHeight(el);
                        $jq(el).on('input', function() { adjustHeight(this); });
                    });
                }

                var $textareas = $jq('textarea.autosize');
                if ($textareas.length > 0) { initAutosize($textareas); }

                $jq(document).on('formset:added', function(event, $row) {
                    var $newFields = $row.find('textarea.autosize');
                    if ($newFields.length > 0) { initAutosize($newFields); }
                });
            });
        }
    }

    // ================================================================
    // 7. Inline Formset Init (Obsługa Stacked & Tabular bez inline script)
    // ================================================================
    {
        // Wybór odpowiedniej instancji jQuery (priorytet dla django.jQuery z pluginem formset)
        const $jq = (typeof django !== 'undefined' && django.jQuery) ? django.jQuery : (window.Suit ? window.Suit.$ : window.jQuery);
        if ($jq) {
            $jq(document).ready(function() {

                // --- Funkcje pomocnicze dla inline (z oryginalnych szablonów) ---
                var updateInlineLabel = function(row, rowsSelector) {
                     $jq(rowsSelector).find(".inline_label").each(function(i) {
                        var count = i + 1; $jq(this).html($jq(this).html().replace(/(#\d+)/g, "#" + count));
                    });
                };

                var reinitDateTimeShortCuts = function() {
                    if (typeof DateTimeShortcuts != "undefined") {
                        $jq(".datetimeshortcuts").remove();
                        DateTimeShortcuts.init();
                    }
                };

                var updateSelectFilter = function() {
                    if (typeof SelectFilter != "undefined"){
                        $jq(".selectfilter").each(function(index, value){
                            var namearr = value.name.split('-');
                            SelectFilter.init(value.id, namearr[namearr.length-1], false, "/static/admin/");
                        });
                        $jq(".selectfilterstacked").each(function(index, value){
                            var namearr = value.name.split('-');
                            SelectFilter.init(value.id, namearr[namearr.length-1], true, "/static/admin/");
                    });
                    }
                };

                var initPrepopulatedFields = function(row) {
                    row.find('.prepopulated_field').each(function() {
                        var field = $jq(this);
                        var input = field.find('input, select, textarea');
                        var dependency_list = input.data('dependency_list') || [];
                        var dependencies = [];
                        $jq.each(dependency_list, function(i, field_name) {
                            dependencies.push('#' + row.find('.form-row .field-' + field_name).find('input, select, textarea').attr('id'));
                        });
                        if (dependencies.length) {
                            input.prepopulate(dependencies, input.attr('maxlength'));
                        }
                    });
                };

                // --- Inicjalizacja formularzy na podstawie konfiguracji w HTML ---
                $jq('.js-inline-admin-formset-config').each(function() {
                        var $config = $jq(this);
                        var prefix = $config.data('prefix');

                    // Pobieramy teksty z atrybutów lub ustawiamy domyślne
                    var addText = $config.data('add-text') || "Add another";
                    var deleteText = $config.data('delete-text') || "Remove";

                    // [FIX] Przywrócenie polskich napisów dla konkretnego prefixu 'files' (zgodnie z oryginałem)
                    if (prefix === 'files') {
                        addText = "Dodaj Plik";
                        deleteText = "Usuń";
                    }

                    // Selektor wierszy (wspólny dla Tabular i Stacked)
                    var rowsSelector = "#" + prefix + "-group .inline-related";

                    // Fallback: jeśli nie znaleziono wierszy .inline-related, szukamy głównego kontenera grupy
                    if ($jq(rowsSelector).length === 0 && $jq("#" + prefix + "-group").length > 0) {
                         rowsSelector = "#" + prefix + "-group";
                    }

                    // Uruchomienie pluginu formset
                    $jq(rowsSelector).formset({
                        prefix: prefix,
                        addText: addText,
                        formCssClass: "dynamic-" + prefix,
                        deleteCssClass: "inline-deletelink",
                        deleteText: deleteText,
                        emptyCssClass: "empty-form",
                        removed: function(row) {
                            updateInlineLabel(row, rowsSelector);
                        },
                        added: function(row) {
                            initPrepopulatedFields(row);
                            reinitDateTimeShortCuts();
                            updateSelectFilter();
                            updateInlineLabel(row, rowsSelector);
                            if (window.Suit && window.Suit.after_inline) {
                                window.Suit.after_inline.run(prefix, row);
                            }
                            // Obsługa Autosize dla nowych wierszy (jeśli występuje)
                            var $nativeJq = window.jQuery || $jq;
                            var $textareas = $nativeJq(row).find('textarea.autosize');
                            if ($textareas.length > 0) {
                                $textareas.trigger('input');
                            }
                        }
            });
                });
            });
        }
    }

    // ================================================================
    // 8. Resource Switcher (File vs Link toggle)
    // ================================================================
    if (typeof django !== 'undefined' && django.jQuery) {
        (function ($) {
            // Funkcja wykonująca logikę przełączania
            function toggleResourceState($container, type) {
                var $switcherInput = $container.find('.js-switcher');
                var $rowFile = $container.find('.field-file');
                var $rowLink = $container.find('.field-link');
                var $rowDataDate = $container.find('.field-data_date');
                var $btnFile = $container.find('.js-switch-to-file');
                var $btnLink = $container.find('.js-switch-to-link');

                $switcherInput.val(type);

                if (type === 'file') {
                    $rowLink.hide();
                    $rowFile.show();
                    $rowDataDate.show();
                    $btnFile.addClass('active');
                    $btnLink.removeClass('active');
                } else {
                    $rowFile.hide();
                    $rowDataDate.hide();
                    $rowLink.show();
                    $btnLink.addClass('active');
                    $btnFile.removeClass('active');
                }
            }

            $(document).ready(function () {
                // Inicjalizacja stanu
                $('.js-switcher').each(function () {
                    var $input = $(this);
                    var $container = $input.closest('fieldset');
                    var currentValue = $input.val() || 'file';
                    toggleResourceState($container, currentValue);
                });

                // Obsługa kliknięć
                $(document).on('click', '.js-switch-to-file', function (e) {
                    var $container = $(this).closest('fieldset');
                    toggleResourceState($container, 'file');
                });

                $(document).on('click', '.js-switch-to-link', function (e) {
                    var $container = $(this).closest('fieldset');
                    toggleResourceState($container, 'link');
                });
            });
        }(django.jQuery));
    }

});
