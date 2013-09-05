define(['libs/jquery'], function () {

    /*
     * MultipleSelect - an alternative to QuickSelect
     * ----------------------------------------------
     *
     * Todo:
     * - Get rid of the rigid html format.
     * - Original attributes on options are lost
     * - The redraw is simple and slow, make it more efficient.
     *
     * This plugin depends on some formatting from the template.
     * It expects:
     * - A container with the class 'multiple-select-container' where
     *   the two multi selects reside.
     * - Two multi selects inside two containers with the classes
     *   '.multiple-select-choices' and '.multiple-select-initial'.
     *   Choices are what the user can add and initial is the initial state.
     * - Everything must be wrapped in a form.
     *
     */

    function MultipleSelect() {
        this.container = $('.multiple-select-container');

        this.form = this.container.parents('form:first');
        this.addSubmitHandler();

        this.choiceNodeSelector = '.multiple-select-choices';
        this.initialNodeSelector = '.multiple-select-initial';
        this.choiceNode = $(this.choiceNodeSelector).find('select');
        this.initialNode = $(this.initialNodeSelector).find('select');

        // Create the data structures
        this.orig_choices = this.createDataStructure(this.choiceNode);
        this.choices = this.createDataStructure(this.choiceNode);
        this.initial = this.createDataStructure(this.initialNode);

        this.addClickListeners();
        this.searchfield = this.container.find($("[type='search']"));
        if (this.searchfield.length) {
            this.addSearchListener();
        }
    }

    MultipleSelect.prototype = {
        createDataStructure: function ($node) {
            /* Create objects from the options */
            var choices = {};
            $node.find('option').each(function (index, element) {
                var $element = $(element);
                choices[$element.val()] = $element.html();
            });
            return choices;
        },
        addClickListeners: function () {
            /* Add click listeners that detect when an option is clicked */
            var self = this;
            this.container.on('click', 'option', function (event) {
                self.move($(event.target));
            });
        },
        move: function ($node) {
            /* Move this node from one select to the other */
            this.switchPlace($node);
            this.reDraw();
        },
        switchPlace: function ($node) {
            /* Switches the node from choice to inital list and vice versa */
            var id = $node.val(), html = $node.html();
            if (this.isChoiceNode($node)) {
                this.initial[id] = html;
                delete this.choices[id];
                delete this.orig_choices[id];
            } else {
                this.choices[id] = html;
                this.orig_choices[id] = html;
                delete this.initial[id];
            }
        },
        isChoiceNode: function ($node) {
            var $parent = $node.parents('div:first');
            return '.' + $parent.attr('class') === this.choiceNodeSelector;
        },
        reDraw: function () {
            /* Redraw the selects */
            this.choiceNode.empty();
            this.initialNode.empty();

            this.appendNodes(this.sortByValue(this.choices), this.choiceNode);
            this.appendNodes(this.sortByValue(this.initial), this.initialNode);
        },
        sortByValue: function (options) {
            /* Sort the options by value => [[key, value], [key, value]] */
            var sortable = [];
            for (var key in options) {
                sortable.push([key, options[key]]);
            }
            sortable.sort(function (a, b) {
                return a[1].localeCompare(b[1]);
            });
            return sortable;
        },
        appendNodes: function (values, $node) {
            for (var i=0; i<values.length; i++) {
                $node.append($('<option/>').val(values[i][0]).html(values[i][1]));
            }
        },
        addSubmitHandler: function () {
            /* Selects all elements in the initial node so that it is
               sent in the post request */
            var self = this;
            this.form.submit(function () {
                self.initialNode.find('option').prop('selected', true);
            });
        },
        addSearchListener: function () {
            var self = this;
            this.searchfield.on('keyup', function () {
                self.doSearch.call(self);
            });
        },
        doSearch: function () {
            /* Search if searchstring is long enough. If we backspace, display all */
            var searchstring = this.searchfield.val();
            if (searchstring.length >= 3) {
                this.choices = this.search(searchstring, this.orig_choices);
                this.reDraw();
            } else if (Object.keys(this.choices).length !== Object.keys(this.orig_choices).length) {
                this.choices = $.extend({}, this.orig_choices);
                this.reDraw();
            }
        },
        search: function (word, data) {
            var searchResult = {};
            for (var key in data) {
                if (data.hasOwnProperty(key)) {
                    if (data[key].match(word)) {
                        searchResult[key] = data[key];
                    }
                }
            }
            return searchResult;
        }
    };

    return MultipleSelect;

});
