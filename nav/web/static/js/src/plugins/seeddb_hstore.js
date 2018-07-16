define([
    "libs-amd/text!resources/seeddb/hstore_container.html",
    "libs-amd/text!resources/seeddb/hstore_row.html",
    'libs/handlebars'
],
function (hstore_container_source, hstore_row_source, Handlebars) {
    /*
     An HStore field displays in the form of a textarea with a dict in it.
     This module parses the dict, and presents a form to the user for editing
     the dict and adding and deleting key-value pairs.
     */
    function HstoreForm($element) {
        var $container = $element.parent(),
            pairs = this.parseDict($element.val()),
            that = this;

        $element.hide();

        /* Compile templates */
        this.hstore_container_template = Handlebars.compile(hstore_container_source);
        this.hstore_row_template = Handlebars.compile(hstore_row_source);

        /* Create container for input fields. Add button for adding rows. */
        this.hstore_container = $(this.hstore_container_template());
        $container.append(this.hstore_container);
        this.addDeleteListener();
        this.addNewRowListener();
        $container.append(this.createAddButton());

        /* Append the existing input fields */
        this.appendRows(pairs);

        /* Update textarea on form submit */
        var form = $($element.parents('form')[0]);
        form.submit(function (event) {
            that.writeDict($container, $element);
        });
    }

    HstoreForm.prototype = {
        'parseDict': function (dict) {
            var obj, keys = [], objs = [];
            obj = dict ? JSON.parse(dict) : {};
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) {
                    keys.push(key);
                }
            }
            keys.sort();
            for (var i = 0, l = keys.length; i < l; i++) {
                objs.push({'key': keys[i], 'value': obj[keys[i]]});
            }
            return objs;
        },
        'createAddButton': function () {
            var that = this,
                button = $('<a class="button small secondary" href="javascript:void(0);">Add row</a>');

            button.on('click', function () {
                that.addRow();
            });
            return button;
        },
        'addDeleteListener': function () {
            this.hstore_container.on('click', '.button.remove-hstore-row', function (event) {
                $($(event.target).parents('.row')[0]).remove();
            });
        },
        'addNewRowListener': function () {
            /* Automatically add a new row if the last value field got focus
               and the key attribute is not empty */
            var that = this;
            this.hstore_container.on('keyup', '.hstore_value', function (event) {
                var value_fields = that.hstore_container.find('.hstore_value');
                if (event.target === value_fields[value_fields.length - 1] && event.target.value.length > 0) {
                    that.addRow();
                }
            });
        },
        'addRow': function (data) {
            if (data === undefined) {
                data = {key: '', value: ''};
            }
            this.hstore_container.append(this.hstore_row_template(data));
        },
        'removeRow': function () {

        },
        'appendRows': function (pairs) {
            for (var i = 0, l = pairs.length; i < l; i++) {
                this.addRow(pairs[i]);
            }
            this.addRow();
        },
        'writeDict': function ($container, $element) {
            var data = {};
            $container.find('.hstoreValues div.row').each(function () {
                var $inputs = $(this).find('input'),
                    key = $inputs[0].value;
                if (key) {
                    data[key] = $inputs[1].value;
                }
            });
            $element.val(JSON.stringify(data));
        }
    };

    return HstoreForm;

});
