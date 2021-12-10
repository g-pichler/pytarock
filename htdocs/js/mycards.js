class CardCollection {
    callback = null;
    shadowed = false;

    static options = {
        animationSpeed: 500,
    };

    parent = null;
    cards = [];

    get length() {
        return this.cards.length;
    }

    get empty() {
        return (this.length === 0);
    }

    shadow() {
        this.shadowed = true;
        this.cards.forEach(function (c) {c.shadow()});
    }

    unshadow() {
        this.shadowed = false;
        this.cards.forEach(function (c) {c.unshadow()});
    }

    setClick(callback) {
        this.callback = callback;
        this.cards.forEach(function (c) {c.setClick(callback)});
    }

    unsetClick() {
        this.setClick(null);
    }

    setOptions(options = {}) {
        CardCollection.options = Object.assign({}, CardCollection.options, options);
    }

    constructor(parentID, cards=[], callback=null) {
        this.parent = document.getElementById(parentID);
        this.callback = callback;
        if (! this.parent) {
            console.error("Parent ID #" + parentID + " not found");
        }
        this.addCards(cards);

    }

    addCards(cards) {
        let self = this;
        cards.forEach(function (c) {self.addCard(c)});
    }

    addCard(card) {
        card._setCollection(this);
        card.setClick(this.callback);
        if (this.shadowed) {
            card.shadow();
        }
        this.cards.push(card);

    }

    removeCard(card) {
        card._unsetCollection();
        card.unsetClick();
        card.unshadow();
        delete this.cards[this.cards.indexOf(card)];
    }

    wipe() {
        while (!this.empty) {
            let card = this.cards.pop();
            card.unsetCollection();
        }
    }


}

class Card {
    cls = null;
    wrappercls = null;
    attr = new Set();
    suit = null;
    rank = 0;
    collection = null;
    suit_num = 0;
    suit_numbers = {null: 0,
        'h': 1,
        'd': 2,
        'c': 3,
        's': 4,
        't': 5};

    constructor(suit=null, rank=0, cls='playingcard', wrappercls='cardWrapper') {
        this.cls = cls;
        this.wrapper = document.createElement('div');
        this.wrapper.className = wrappercls;
        this.wrappercls = wrappercls;
        this.div = document.createElement('div');
        this.wrapper.appendChild(this.div);
        this.setSuitRank(suit, rank);
    }

    get valueOf() {
        return this.suit_num * 100 + this.rank;
    }

    setClick(callback) {
        if (callback === null) {
            this.div.onclick = null;
            this.attr.delete("clickable");
        }
        else {
            let self = this;
            this.div.onclick = function () {
                callback(self)
            };
            this.attr.add("clickable");
        }
        this.updateDiv();
    }

    unsetClick(){
        this.setClick(null)
    }

    setSuitRank(suit, rank) {
        if (suit !== null) {
            suit = suit.toLowerCase()
        }
        this.suit = suit;
        this.suit_num = this.suit_numbers[suit]
        this.rank = rank;
        this.updateDiv()
    }

    getString() {
        return this.suit.toUpperCase() + this.rank;
    }

    updateDiv() {
        let shortname = "";
        if (this.suit !== null && this.rank !== 0) {
            shortname = this.suit + '-' + this.rank;
        }
        this.div.className = [...this.attr, this.cls, shortname].join(" ");
    }

    _unsetCollection() {
        this.collection.parent.removeChild(this.wrapper);
        this.collection = null;
    }

    unsetCollection() {
        if (this.collection !== null) {
            this.collection.removeCard(this);
        }
    }

    _setCollection(collection) {
        if (this.collection !== null) {
            // We Move from one to another collection
            this.collection.removeCard(this)
        }
        this.collection = collection
        this.collection.parent.appendChild(this.wrapper);
    }

    setCollection(collection) {
        collection.add(this);
    }

    shadow() {
        this.attr.add("shadow");
        this.updateDiv()
    }

    unshadow() {
        this.attr.delete('shadow');
        this.updateDiv()
    }

}