define(['libs/jquery'], function () {

    function MultipleSelect() {
        this.container = $('.multiple-select-container');
        this.form = this.container.parents('form:first');
        this.addSubmitHandler();
        this.choiceNodeSelector = '.multiple-select-choices';
        this.initialNodeSelector = '.multiple-select-initial';
        this.choiceNode = $(this.choiceNodeSelector).find('select');
        this.initialNode = $(this.initialNodeSelector).find('select');
        this.choices = this.createDataStructure(this.choiceNode);
        this.initial = this.createDataStructure(this.initialNode);
        this.addClickListeners();
    }

    MultipleSelect.prototype = {
        createDataStructure: function ($node) {
            var choices = {};
            $node.find('option').each(function (index, element) {
                var $element = $(element);
                choices[$element.val()] = $element.html();
            });
            return choices;
        },
        addClickListeners: function () {
            var self = this;
            this.container.on('click', 'option', function (event) {
                self.move($(event.target));
            });
        },
        move: function ($node) {
            this.switchPlace($node);
            this.reDraw();
        },
        switchPlace: function ($node) {
            var id = $node.val(), html = $node.html();
            if (this.isChoiceNode($node)) {
                this.initial[id] = html;
                delete this.choices[id];
            } else {
                this.choices[id] = html;
                delete this.initial[id];
            }
        },
        isChoiceNode: function ($node) {
            var $parent = $node.parents('div:first');
            return '.' + $parent.attr('class') === this.choiceNodeSelector;
        },
        reDraw: function () {
            this.choiceNode.empty();
            this.initialNode.empty();

            this.appendNodes(this.sortByValue(this.choices), this.choiceNode);
            this.appendNodes(this.sortByValue(this.initial), this.initialNode);
        },
        sortByValue: function (options) {
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
            var self = this;
            this.form.submit(function () {
                self.initialNode.find('option').prop('selected', true);
            });
        }
    };

    return MultipleSelect;

});
