define(['tinysort'], function (tinysort) {

    /**
     * MultipleSelect - an alternative to QuickSelect
     * ----------------------------------------------
     *
     * Todo:
     * - Get rid of the rigid html format.
     * - The redraw is simple and slow, make it more efficient.
     *
     * This plugin depends on some formatting from the template.
     * It expects:
     * - A container with the class 'multiple-select-container' where
     *   the two multi selects reside.
     * - Two multi selects with the classes
     *   '.multiple-select-choices' and '.multiple-select-initial'.
     *   Choices are what the user can add and initial is the initial state.
     * - Everything must be wrapped in a form.
     *
     */

    function MultipleSelect(config) {
        if (typeof config === 'undefined') {
            config = {};
        }

        this.containerSelector = config.containerNodeSelector || '.multiple-select-container';
        this.container = $(this.containerSelector);
        this.choiceNodeSelector = config.choiceNodeSelector || '.multiple-select-choices';
        this.initialNodeSelector = config.initialNodeSelector || '.multiple-select-initial';
        this.choiceNode = $(this.choiceNodeSelector);
        this.initialNode = $(this.initialNodeSelector);

        if (!(this.container.length && this.choiceNode.length && this.initialNode.length)) {
            console.error('Could not find needed elements');
            return;
        }

        this.form = this.container.parents('form:first');
        this.addSubmitHandler();

        // Create the data structures
        this.findOptions();
        this.orig_choices = this.choiceNode.clone();

        this.addClickListeners();
        this.searchfield = config.searchField || this.container.find($("[type='search']"));
        if (this.searchfield.length) {
            this.addSearchListener();
        }
    }

    MultipleSelect.prototype = {
        findOptions: function () {
            this.findChoiceOptions();
            this.findInitialOptions();
        },
        findChoiceOptions: function () {
            this.choices = this.choiceNode.find('option');
        },
        findInitialOptions: function () {
            this.initial = this.initialNode.find('option');
        },
        addClickListeners: function () {
            /* Add click listeners that detect when an option is clicked */
            var self = this;
            this.container.on('click', 'option', function (event) {
                self.move($(event.target));
            });
        },
        move: function ($node) {
            /* Switches the node from choice to inital list and vice versa */
            if ($node.parent().is(this.choiceNode)) {
                $node.appendTo(this.initialNode);
                $node.prop('selected', false);
                this.orig_choices.find('[value="' + $node.val() + '"]').remove();
                this.sortInitial();
            } else if ($node.parent().is(this.initialNode)) {
                $node.appendTo(this.choiceNode);
                $node.prop('selected', false);
                this.orig_choices.append($node.clone());
                this.sortChoices();
            } else {
                console.log($node);
                console.error("Could not find parent of " + $node);
            }
        },
        compareElements: function(a, b) {
            return a.innerHTML.toLowerCase().localeCompare(b.innerHTML.toLowerCase());
        },
        sortInitial: function () {
            this.findInitialOptions();
            const initialOptions = Array.from(this.initialNode[0].options);
            const sortedOptions = tinysort(initialOptions, {selector: null, order: 'asc', natural: true});
            this.initialNode.empty();
            for (const option of sortedOptions) {
                this.initialNode[0].appendChild(option);
            }
        },
        sortChoices: function () {
            this.findChoiceOptions();
            const choiceOptions = Array.from(this.choiceNode[0].options);
            const sortedOptions = tinysort(choiceOptions, {selector: null, order: 'asc', natural: true});
            this.choiceNode.empty();
            for (const option of sortedOptions) {
                this.choiceNode[0].appendChild(option);
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

            if (searchstring.length < 3) {
                if (this.choices.length !== this.orig_choices.find('option').length) {
                    this.choices = this.orig_choices.find("option").clone();
                    this.reDraw();
                }
            } else {
                this.choices = this.orig_choices.find("option:contains('" + searchstring + "')").clone();
                this.reDraw();
            }

        },
        reDraw: function () {
            /* Redraw the selects */
            this.choiceNode.empty();
            this.choiceNode.append(this.choices);
        }
    };

    return MultipleSelect;

});
