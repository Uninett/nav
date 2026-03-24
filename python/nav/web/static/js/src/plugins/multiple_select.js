define([], function () {

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

    const collator = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true });

    function sortOptions(selectElement) {
        const options = [...selectElement.options];
        options.sort((a, b) => collator.compare(a.textContent, b.textContent));
        for (const option of options) {
            selectElement.appendChild(option);
        }
    }

    function MultipleSelect(config = {}) {
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
        findOptions() {
            this.findChoiceOptions();
            this.findInitialOptions();
        },
        findChoiceOptions() {
            this.choices = this.choiceNode.find('option');
        },
        findInitialOptions() {
            this.initial = this.initialNode.find('option');
        },
        addClickListeners() {
            this.container.on('click', 'option', (event) => {
                this.move($(event.target));
            });
        },
        move($node) {
            if ($node.parent().is(this.choiceNode)) {
                $node.appendTo(this.initialNode);
                $node.prop('selected', false);
                this.orig_choices.find('[value="' + $node.val() + '"]').remove();
                sortOptions(this.initialNode[0]);
            } else if ($node.parent().is(this.initialNode)) {
                $node.appendTo(this.choiceNode);
                $node.prop('selected', false);
                this.orig_choices.append($node.clone());
                sortOptions(this.choiceNode[0]);
            } else {
                console.error("Could not find parent of ", $node);
            }
        },
        addSubmitHandler() {
            this.form.submit(() => {
                this.initialNode.find('option').prop('selected', true);
            });
        },
        addSearchListener() {
            this.searchfield.on('keyup', () => {
                this.doSearch();
            });
        },
        doSearch() {
            const searchstring = this.searchfield.val();

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
        reDraw() {
            this.choiceNode.empty();
            this.choiceNode.append(this.choices);
        }
    };

    return MultipleSelect;

});
