/* TODO: Rewrite during rewrite of multiple-select
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

            it('should create a list of option elements', function () {
            assert.equal(this.mselect.choices.length, 3);
            });
            it('should find correct parent node on choices', function () {
                var $node = $('.multiple-select-choices option:first');
                assert.isTrue(this.mselect.isChoiceNode($node));
            });
            it('should find correct parent node on initial', function () {
                var $node = $('.multiple-select-initial option:first');
                assert.isFalse(this.mselect.isChoiceNode($node));
            });
            describe('move', function () {
                it('should move option from choice to inital', function () {
                    var $node = $('.multiple-select-choices option:first');
                    this.mselect.move($node);
                    assert.equal(this.mselect.choiceNode.find('option').length, 2);
                    assert.equal(this.mselect.initialNode.find('option').length, 4);
                });
                it('should move option from initial to choice', function () {
                    var $node = $('.multiple-select-initial option:first');
                    this.mselect.move($node);
                    assert.equal(this.mselect.choiceNode.find('option').length, 4);
                    assert.equal(this.mselect.initialNode.find('option').length, 2);
                });
            });
            describe('sort', function () {
                it('should sort initial when new node is appended', function () {
                    var $node = $('.multiple-select-choices option:first');
                    this.mselect.move($node);
                    assert.equal($('.multiple-select-initial option:first').val(), '1');
                });
                it('should sort choices when new node is appended', function () {
                    var $node = $('.multiple-select-initial option:first');
                    this.mselect.move($node);
                    assert.equal($('.multiple-select-choices option:last').val(), '9');
                });
            });
            describe('redraw', function () {
                it('should redraw choices sorted on html', function () {
                    this.mselect.reDraw();
                    var keys = [];
                    $(this.mselect.choiceNode).find('option').each(function () {
                        keys.push(this.value);
                    });
                    assert.deepEqual(keys, ['1', '39', '69']);
                });
            });
            describe('search', function () {
                it('should have a searchfield', function () {
                    assert(this.mselect.searchfield.length);
                });
                it('should skip searches that are too short', function () {
                    this.mselect.searchfield.val('ab').keyup();
                    assert.strictEqual(this.mselect.choiceNode.find('option').length, 3);
                });
                it('should do searches on third character', function () {
                    this.mselect.searchfield.val('bla').keyup();
                    assert.equal(this.mselect.choices.length, 1);
                });
                it('should display all results when backspacing to less than 3 chars', function () {
                    this.mselect.searchfield.val('bla').keyup();
                    this.mselect.searchfield.val('bl').keyup();
                    assert.strictEqual(this.mselect.choiceNode.find('option').length, 3);
                });
                it('should return matches based on values not keys', function () {
                    this.mselect.searchfield.val('uninett').keyup();
                    assert.equal(this.mselect.choiceNode.find('option').length, 2);
                });
                it('should return to original after search and move', function () {
                    this.mselect.searchfield.val('bla').keyup();
                    this.mselect.move(this.mselect.choices.eq(0));
                    this.mselect.searchfield.val('').keyup();
                    assert.equal(this.mselect.choiceNode.find('option').length, 2);
                });
            });
        });
    }
);
*/
