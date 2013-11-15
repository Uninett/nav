define(['libs/jquery', 'libs/jquery.tinysort'], function () {

    /*
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
        this.findOptions();
        this.orig_choices = this.choiceNode.clone();

        this.addClickListeners();
        this.searchfield = this.container.find($("[type='search']"));
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
            if (this.isChoiceNode($node)) {
                $node.appendTo(this.initialNode);
                $node.prop('selected', false);
                this.orig_choices.find('[value="' + $node.val() + '"]').remove();
                this.sortInitial();
            } else {
                $node.appendTo(this.choiceNode);
                $node.prop('selected', false);
                this.orig_choices.append($node.clone());
                this.sortChoices();
            }
        },
        isChoiceNode: function ($node) {
            var $parent = $node.parents('div:first'),
                classList = $parent.attr('class').split(/\s+/);
            for (var i=0; i<classList.length; i++) {
                if ('.' + classList[i] === this.choiceNodeSelector) {
                    return true;
                }
            }
            return false;
        },
        sortInitial: function () {
            this.findInitialOptions();
            this.initial.tsort();
        },
        sortChoices: function () {
            this.findChoiceOptions();
            this.choices.tsort();
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
