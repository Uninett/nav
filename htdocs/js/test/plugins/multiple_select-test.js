define(['plugins/multiple-select',
    'libs-amd/text!testResources/templates/multipleselect.html',
    'libs/jquery'],
    function (MultipleSelect, html) {
        describe("MultipleSelect", function () {
            beforeEach(function () {
                $('body').empty();
                $('body').html(html);
                this.mselect = new MultipleSelect();
            });

            it('should create datastructure from options', function () {
                assert.deepEqual(
                    this.mselect.choices,
                    {1: 'absint.online.ntnu.no', 39: 'blaasal-sw.uninett.no', 69: 'buick.lab.uninett.no'}
                );
            });
            it('should create datastructure from initial', function () {
                assert.deepEqual(
                    this.mselect.initial,
                    {9: 'kanari.uninett.no', 12: 'mi6-old.uninett.no', 34: 'ufisa.uninett.no'}
                );
            });
            it('should find correct parent node on choices', function () {
                var $node = $('.multiple-select-choices option:first');
                assert.isTrue(this.mselect.isChoiceNode($node));
            });
            it('should find correct parent node on initial', function () {
                var $node = $('.multiple-select-initial option:first');
                assert.isFalse(this.mselect.isChoiceNode($node));
            });
            describe('switchnodes', function () {
                it('should switch dictionary from choice to initial', function () {
                    var $node = $('.multiple-select-choices option:first');
                    this.mselect.switchPlace($node);
                    assert.deepEqual(this.mselect.initial, {1: 'absint.online.ntnu.no', 9: 'kanari.uninett.no', 12: 'mi6-old.uninett.no', 34: 'ufisa.uninett.no'});
                    assert.deepEqual(this.mselect.choices, {39: 'blaasal-sw.uninett.no', 69: 'buick.lab.uninett.no'});
                });
                it('should switch dictionary from initial to choice', function () {
                    var $node = $('.multiple-select-initial option:first');
                    this.mselect.switchPlace($node);
                    assert.deepEqual(this.mselect.initial, {12: 'mi6-old.uninett.no', 34: 'ufisa.uninett.no'});
                    assert.deepEqual(this.mselect.choices, {1: 'absint.online.ntnu.no', 9: 'kanari.uninett.no', 39: 'blaasal-sw.uninett.no', 69: 'buick.lab.uninett.no'});
                });
            });
            it('should sort dict by value', function () {
                assert.deepEqual(
                    this.mselect.sortByValue({1: 'b', 2: 'a'}),
                    [['2', 'a'], ['1', 'b']]
                );
            });
            describe('redraw', function () {
                it('should redraw choices sorted on html', function () {
                    this.mselect.reDraw();
                    var keys = [];
                    $(this.mselect.choiceNodeSelector).find('option').each(function () {
                        keys.push(this.value);
                    });
                    assert.deepEqual(keys, ['1', '39', '69']);
                });
            });
            describe('search', function () {
                beforeEach(function () {
                    this.testdata = {1: 'ajaua', 2: 'mjaus', 3: 'blapp'};
                });
                it('should have a searchfield', function () {
                    assert(this.mselect.searchfield.length);
                });
                it('should skip searches that are too short', function () {
                    this.mselect.searchfield.val('ab').keyup();
                    assert.deepEqual(
                        this.mselect.choices,
                        {1: 'absint.online.ntnu.no', 39: 'blaasal-sw.uninett.no', 69: 'buick.lab.uninett.no'}
                    );
                });
                it('should do searches on third character', function () {
                    this.mselect.searchfield.val('bla').keyup();
                    assert.deepEqual(this.mselect.choices, {39: 'blaasal-sw.uninett.no'});
                });
                it('should display all results when backspacing to less than 3 chars', function () {
                    this.mselect.searchfield.val('bla').keyup();
                    this.mselect.searchfield.val('bl').keyup();
                    assert.strictEqual(this.mselect.choiceNode.find('option').length, 3);
                });
                it('should return matches based on values not keys', function () {
                    assert.deepEqual(this.mselect.search('jau', this.testdata), {1: 'ajaua', 2: 'mjaus'});
                });
            });
        });
    }
);
