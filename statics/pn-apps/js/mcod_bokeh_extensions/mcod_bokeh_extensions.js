/*!
 * Copyright (c) 2012 - 2020, Anaconda, Inc., and Bokeh Contributors
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * Neither the name of Anaconda nor the names of any contributors
 * may be used to endorse or promote products derived from this software
 * without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
 * THE POSSIBILITY OF SUCH DAMAGE.
*/
(function(root, factory) {
  factory(root["Bokeh"], undefined);
})(this, function(Bokeh, version) {
  var define;
  return (function(modules, entry, aliases, externals) {
    const bokeh = typeof Bokeh !== "undefined" && (version != null ? Bokeh[version] : Bokeh);
    if (bokeh != null) {
      return bokeh.register_plugin(modules, entry, aliases);
    } else {
      throw new Error("Cannot find Bokeh " + version + ". You have to load it prior to loading plugins.");
    }
  })
({
"0ee310a845": /* index.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const bootstrap_select_1 = require("4e0e830bc9") /* ./widgets/bootstrap_select */;
    const localized_hover_tool_1 = require("65b19704f1") /* ./tools/localized_hover_tool */;
    const localized_pan_tool_1 = require("1f74824544") /* ./tools/localized_pan_tool */;
    const localized_save_tool_1 = require("cf96e53285") /* ./tools/localized_save_tool */;
    const localized_wheel_zoom_tool_1 = require("bc864251f1") /* ./tools/localized_wheel_zoom_tool */;
    const localized_reset_tool_1 = require("f0a5ee67b8") /* ./tools/localized_reset_tool */;
    const extendedcolumn_1 = require("ab9995ef6b") /* ./layouts/extendedcolumn */;
    const base_1 = require("@bokehjs/base");
    base_1.register_models({ BootstrapSelect: bootstrap_select_1.BootstrapSelect, LocalizedHoverTool: localized_hover_tool_1.LocalizedHoverTool, LocalizedPanTool: localized_pan_tool_1.LocalizedPanTool,
        LocalizedSaveTool: localized_save_tool_1.LocalizedSaveTool, LocalizedWheelZoomTool: localized_wheel_zoom_tool_1.LocalizedWheelZoomTool, LocalizedResetTool: localized_reset_tool_1.LocalizedResetTool, ExtendedColumn: extendedcolumn_1.ExtendedColumn });
},
"4e0e830bc9": /* widgets/bootstrap_select.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const input_widget_1 = require("@bokehjs/models/widgets/input_widget");
    const dom_1 = require("@bokehjs/core/dom");
    //import { isString } from "core/util/types";
    // import { bk_input } from "styles/widgets/inputs";
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class BootstrapSelectView extends input_widget_1.InputWidgetView {
        connect_signals() {
            super.connect_signals();
            this.connect(this.model.properties.value.change, () => this.render_selection());
        }
        render() {
            super.render();
            const options = this.model.options.map((opts) => {
                let _label, _d, value, title;
                let data = {};
                [_label, _d] = opts;
                [value, data.subtext] = _d;
                title = _label;
                if (data.subtext)
                    title = data.subtext;
                return dom_1.option({ value, data, title }, _label);
            });
            this.select_el = dom_1.select({
                multiple: true,
                title: this.model.alt_title,
                disabled: false,
            }, options);
            this.group_el.appendChild(this.select_el);
            this.render_selection();
            let select_opts = {};
            select_opts.title = this.model.alt_title;
            select_opts.actionsBox = this.model.actions_box;
            select_opts.liveSearch = this.model.live_search;
            //select_opts.showSubtext = this.model.show_subtext;
            if (this.model.count_selected_text)
                select_opts.countSelectedText = this.model.count_selected_text;
            if (this.model.none_selected_text)
                select_opts.noneSelectedText = this.model.none_selected_text;
            if (this.model.selected_text_format)
                select_opts.selectedTextFormat = this.model.selected_text_format;
            if (this.model.none_results_text)
                select_opts.noneResultsText = this.model.none_results_text;
            jQuery(this.select_el).selectpicker(select_opts);
            if (this.model.select_all_at_start)
                jQuery(this.select_el).selectpicker("selectAll");
            setTimeout(() => {
                jQuery('ul.dropdown-menu').addClass('dropdown__list');
                jQuery('ul.dropdown-menu').children('li').addClass('dropdown-item');
                jQuery('select.bk').on('show.bs.select', () => {
                    jQuery('ul.dropdown-menu').children('li').addClass('dropdown-item');
                });
                jQuery('button.dropdown-toggle').removeClass('btn-light');
            });
            this.select_el.addEventListener("change", () => this.change_input());
        }
        render_selection() {
            const ids = new Set(this.model.value.map((v) => {
                return v[0].toString();
            }));
            for (const el of Array.from(this.el.querySelectorAll("option"))) {
                el.selected = ids.has(el.value);
            }
        }
        change_input() {
            const values = [];
            for (const el of this.el.querySelectorAll("option")) {
                if (el.selected) {
                    const opts = this.model.options.filter((item) => item[1][0] == el.value);
                    for (let opt of opts) {
                        values.push(opt[1]);
                    }
                    jQuery(el).parent().addClass('active');
                }
            }
            this.model.value = values;
            super.change_input();
        }
    }
    exports.BootstrapSelectView = BootstrapSelectView;
    BootstrapSelectView.__name__ = "BootstrapSelectView";
    class BootstrapSelect extends input_widget_1.InputWidget {
        constructor(attrs) {
            super(attrs);
        }
        static init_BootstrapSelect() {
            this.prototype.default_view = BootstrapSelectView;
            this.define({
                alt_title: [p.String, ""],
                value: [p.Array, []],
                options: [p.Array, []],
                actions_box: [p.Boolean, false],
                live_search: [p.Boolean, false],
                // show_subtext: [p.Boolean, false],
                select_all_at_start: [p.Boolean, false],
                none_selected_text: [p.String, ""],
                count_selected_text: [p.String, ""],
                selected_text_format: [p.String, ""],
                none_results_text: [p.String, ""],
            });
        }
    }
    exports.BootstrapSelect = BootstrapSelect;
    BootstrapSelect.__name__ = "BootstrapSelect";
    BootstrapSelect.__module__ = "mcod.pn_apps.bokeh.widgets";
    BootstrapSelect.init_BootstrapSelect();
},
"65b19704f1": /* tools/localized_hover_tool.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const hover_tool_1 = require("@bokehjs/models/tools/inspectors/hover_tool");
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class LocalizedHoverTool extends hover_tool_1.HoverTool {
        constructor(attrs) {
            super(attrs);
            this.tool_name = this.localized_tool_name;
            this.icon = "bk-tool-icon-custom-hover";
        }
        static init_LocalizedHoverTool() {
            this.prototype.default_view = hover_tool_1.HoverToolView;
            this.define({
                localized_tool_name: [p.String],
            });
        }
    }
    exports.LocalizedHoverTool = LocalizedHoverTool;
    LocalizedHoverTool.__name__ = "LocalizedHoverTool";
    LocalizedHoverTool.__module__ = "mcod.pn_apps.bokeh.tools.base";
    LocalizedHoverTool.init_LocalizedHoverTool();
},
"1f74824544": /* tools/localized_pan_tool.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const pan_tool_1 = require("@bokehjs/models/tools/gestures/pan_tool");
    const icons_1 = require("@bokehjs/styles/icons");
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class LocalizedPanTool extends pan_tool_1.PanTool {
        constructor(attrs) {
            super(attrs);
            this.tool_name = this.localized_tool_name;
        }
        static init_LocalizedPanTool() {
            this.prototype.default_view = pan_tool_1.PanToolView;
            this.define({
                localized_tool_name: [p.String],
            });
        }
        get tooltip() {
            return this.tool_name;
        }
        get icon() {
            switch (this.dimensions) {
                case "both": return icons_1.bk_tool_icon_pan;
                case "width": return "bk-tool-icon-custom-pan";
                case "height": return icons_1.bk_tool_icon_ypan;
            }
        }
    }
    exports.LocalizedPanTool = LocalizedPanTool;
    LocalizedPanTool.__name__ = "LocalizedPanTool";
    LocalizedPanTool.__module__ = "mcod.pn_apps.bokeh.tools.base";
    LocalizedPanTool.init_LocalizedPanTool();
},
"cf96e53285": /* tools/localized_save_tool.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const save_tool_1 = require("@bokehjs/models/tools/actions/save_tool");
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class LocalizedSaveTool extends save_tool_1.SaveTool {
        constructor(attrs) {
            super(attrs);
            this.tool_name = this.localized_tool_name;
            this.icon = "bk-tool-icon-custom-save";
        }
        static init_LocalizedSaveTool() {
            this.prototype.default_view = save_tool_1.SaveToolView;
            this.define({
                localized_tool_name: [p.String],
            });
        }
    }
    exports.LocalizedSaveTool = LocalizedSaveTool;
    LocalizedSaveTool.__name__ = "LocalizedSaveTool";
    LocalizedSaveTool.__module__ = "mcod.pn_apps.bokeh.tools.base";
    LocalizedSaveTool.init_LocalizedSaveTool();
},
"bc864251f1": /* tools/localized_wheel_zoom_tool.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const wheel_zoom_tool_1 = require("@bokehjs/models/tools/gestures/wheel_zoom_tool");
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class LocalizedWheelZoomTool extends wheel_zoom_tool_1.WheelZoomTool {
        constructor(attrs) {
            super(attrs);
            this.tool_name = this.localized_tool_name;
            this.icon = "bk-tool-icon-custom-wheel-zoom";
        }
        static init_LocalizedWheelZoomTool() {
            this.prototype.default_view = wheel_zoom_tool_1.WheelZoomToolView;
            this.define({
                localized_tool_name: [p.String],
            });
        }
        get tooltip() {
            return this.tool_name;
        }
    }
    exports.LocalizedWheelZoomTool = LocalizedWheelZoomTool;
    LocalizedWheelZoomTool.__name__ = "LocalizedWheelZoomTool";
    LocalizedWheelZoomTool.__module__ = "mcod.pn_apps.bokeh.tools.base";
    LocalizedWheelZoomTool.init_LocalizedWheelZoomTool();
},
"f0a5ee67b8": /* tools/localized_reset_tool.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const reset_tool_1 = require("@bokehjs/models/tools/actions/reset_tool");
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class LocalizedResetTool extends reset_tool_1.ResetTool {
        constructor(attrs) {
            super(attrs);
            this.tool_name = this.localized_tool_name;
            this.icon = "bk-tool-icon-custom-reset";
        }
        static init_LocalizedResetTool() {
            this.prototype.default_view = reset_tool_1.ResetToolView;
            this.define({
                localized_tool_name: [p.String],
            });
        }
    }
    exports.LocalizedResetTool = LocalizedResetTool;
    LocalizedResetTool.__name__ = "LocalizedResetTool";
    LocalizedResetTool.__module__ = "mcod.pn_apps.bokeh.tools.base";
    LocalizedResetTool.init_LocalizedResetTool();
},
"ab9995ef6b": /* layouts/extendedcolumn.js */ function _(require, module, exports) {
    Object.defineProperty(exports, "__esModule", { value: true });
    const tslib_1 = require("tslib");
    const box_1 = require("@bokehjs/models/layouts/box");
    const grid_1 = require("@bokehjs/core/layout/grid");
    const p = tslib_1.__importStar(require("@bokehjs/core/properties"));
    class ExtendedColumnView extends box_1.BoxView {
        render() {
            super.render();
            this.el.setAttribute('aria-hidden', this.model.aria_hidden.toString());
        }
        _update_layout() {
            const items = this.child_views.map((child) => child.layout);
            this.layout = new grid_1.Column(items);
            this.layout.rows = this.model.rows;
            this.layout.spacing = [this.model.spacing, 0];
            this.layout.set_sizing(this.box_sizing());
        }
    }
    exports.ExtendedColumnView = ExtendedColumnView;
    ExtendedColumnView.__name__ = "ExtendedColumnView";
    class ExtendedColumn extends box_1.Box {
        constructor(attrs) {
            super(attrs);
        }
        static init_ExtendedColumn() {
            this.prototype.default_view = ExtendedColumnView;
            this.define(({ Any }) => ({
                rows: [Any /*TODO*/, "auto"],
                aria_hidden: [p.Boolean, false],
            }));
        }
    }
    exports.ExtendedColumn = ExtendedColumn;
    ExtendedColumn.__name__ = "ExtendedColumn";
    ExtendedColumn.__module__ = "mcod.pn_apps.bokeh.layouts";
    ExtendedColumn.init_ExtendedColumn();
},
}, "0ee310a845", {"index":"0ee310a845","widgets/bootstrap_select":"4e0e830bc9","tools/localized_hover_tool":"65b19704f1","tools/localized_pan_tool":"1f74824544","tools/localized_save_tool":"cf96e53285","tools/localized_wheel_zoom_tool":"bc864251f1","tools/localized_reset_tool":"f0a5ee67b8","layouts/extendedcolumn":"ab9995ef6b"}, {});
})

//# sourceMappingURL=mcod_bokeh_extensions.js.map
