const STANDARD = 0;

var cards = (function() {
  //The global options
  var opt = {
    cardSize: {
      width: 70,
      height: 140,
      padding: 40
    },
    animationSpeed: 500,
    table: 'body',
    cardback: 'red',
    acesHigh: false,
    blackJoker: false,
    redJoker: false,
    type: STANDARD,
    loop: 1
  };
  var zIndexCounter = 1;
  var all = []; //All the cards created.
  var start = 1;

  function mouseEvent(ev) {
    var card = $(this).data('card');
    if (card.container) {
      var handler = card.container._click;
      if (handler) {
        handler.func.call(handler.context || window, card, ev);
      }
    }
  }

  function init(options) {
    if (options) {
      for (var i in options) {
        if (opt.hasOwnProperty(i)) {
          opt[i] = options[i];
        }
      }
    }

  }

  function Card(suit, rank, table) {
    this.init(suit, rank, table);
  }

  Card.prototype = {
    init: function(suit, rank, table) {
      this.shortName = suit + rank;
      this.suit = suit;
      this.rank = rank;
      this.name = suit.toUpperCase() + rank;
      this.faceUp = false;
      this.div = $('<div/>')
      this.el = this.div.css({
        width: opt.cardSize.width,
        height: opt.cardSize.height,
        position: 'absolute',
        cursor: 'pointer',
        'background-repeat': 'no-repeat',
        'background-size': 'cover',
      });
      this.div.addClass('card');
      this.div.data('card', this);
      this.div.onclick = mouseEvent;
      this.div.appendTo($(table));
      // this.el.addClass('card ' + suit.toLowerCase() + "-" + rank).data('card', this).appendTo($(table));
      this.showCard();
      this.moveToFront();
    },

    toString: function() {
      return this.name;
    },

    moveTo: function(x, y, speed, callback) {
      var props = {
        top: y - (opt.cardSize.height / 2),
        left: x - (opt.cardSize.width / 2)
      };
      $(this.el).animate(props, speed || opt.animationSpeed, callback);
    },

    rotate: function(angle) {
      $(this.el)
        .css('-webkit-transform', 'rotate(' + angle + 'deg')
        .css('-moz-transform', 'rotate(' + angle + 'deg)')
        .css('-ms-transform', 'rotate(' + angle + 'deg)')
        .css('transform', 'rotate(' + angle + 'deg)')
        .css('-o-transform', 'rotate(' + angle + 'deg)');
    },

    showCard: function() {
      console.log("SHOWING " + this.el)
      this.rotate(0);
      let cls = this.suit.toLowerCase() + "-" + this.rank;
      console.log('Adding class ', cls)
      this.div.addClass(cls);
    },

    hideCard: function(position) {
      this.div.removeClass(this.suit.toLowerCase() + "-" + this.rank);
      this.rotate(0);
    },

    moveToFront: function() {
      $(this.el).css('z-index', zIndexCounter++);
    }
  };

  function Container() {

  }

  Container.prototype = [];
  Container.prototype.extend = function(obj) {
    for (var prop in obj) {
      this[prop] = obj[prop];
    }
  }
  Container.prototype.extend({
    addCard: function(card) {
      this.addCards([card]);
    },

    addCards: function(cards) {
      for (var i = 0; i < cards.length; i++) {
        var card = cards[i];
        if (card.container) {
          card.container.removeCard(card);
        }
        this.push(card);
        card.container = this;
      }
    },

    removeCard: function(card) {
      for (var i = 0; i < this.length; i++) {
        if (this[i] === card) {
          this.splice(i, 1);
          return true;
        }
      }
      return false;
    },

    init: function(options) {
      options = options || {};
      this.x = options.x || $(opt.table).width() / 2;
      this.y = options.y || $(opt.table).height() / 2;
      this.faceUp = options.faceUp;
    },

    click: function(func, context) {
      this._click = {
        func: func,
        context: context
      };
    },

    mousedown: function(func, context) {
      this._mousedown = {
        func: func,
        context: context
      };
    },

    mouseup: function(func, context) {
      this._mouseup = {
        func: func,
        context: context
      };
    },

    render: function(options) {
      options = options || {};
      var speed = options.speed || opt.animationSpeed;
      this.calcPosition(options);
      for (var i = 0; i < this.length; i++) {
        var card = this[i];
        zIndexCounter++;
        card.moveToFront();
        var top = parseInt($(card.el).css('top'));
        var left = parseInt($(card.el).css('left'));
        if (top !== card.targetTop || left !== card.targetLeft) {
          var props = {
            top: card.targetTop,
            left: card.targetLeft,
            queue: false
          };
          if (options.immediate) {
            $(card.el).css(props);
          } else {
            $(card.el).animate(props, speed);
          }
        }
      }
      var me = this;
      var flip = function() {
        for (var i = 0; i < me.length; i++) {
          if (me.faceUp) {
            me[i].showCard();
          } else {
            me[i].hideCard();
          }
        }
      }
      if (options.immediate) {
        flip();
      } else {
        setTimeout(flip, speed / 2);
      }

      if (options.callback) {
        setTimeout(options.callback, speed);
      }
    },

    topCard: function() {
      return this[this.length - 1];
    },

    toString: function() {
      return 'Container';
    }
  });

  function Deck(options) {
    this.init(options);
  }

  Deck.prototype = new Container();
  Deck.prototype.extend({
    calcPosition: function(options) {
      options = options || {};
      var left = Math.round(this.x - opt.cardSize.width / 2, 0);
      var top = Math.round(this.y - opt.cardSize.height / 2, 0);
      var condenseCount = 6;
      for (var i = 0; i < this.length; i++) {
        if (i > 0 && i % condenseCount === 0) {
          top -= 1;
          left -= 1;
        }
        this[i].targetTop = top;
        this[i].targetLeft = left;
      }
    },

    toString: function() {
      return 'Deck';
    },

    deal: function(count, hands, speed, callback) {
      var me = this;
      var i = 0;
      var totalCount = count * hands.length;

      function dealOne() {
        if (me.length === 0 || i === totalCount) {
          if (callback) {
            callback();
          }
          return;
        }
        hands[i % hands.length].addCard(me.topCard());
        hands[i % hands.length].render({
          callback: dealOne,
          speed: speed
        });
        i++;
      }
      dealOne();
    }
  });

  function Hand(options) {
    this.init(options);
  }
  Hand.prototype = new Container();
  Hand.prototype.extend({
    calcPosition: function(options) {
      options = options || {};
      var width = opt.cardSize.width + (this.length - 1) * opt.cardSize.padding;
      var left = Math.round(this.x - width / 2);
      var top = Math.round(this.y - opt.cardSize.height / 2, 0);
      for (var i = 0; i < this.length; i++) {
        this[i].targetTop = top;
        this[i].targetLeft = left + i * opt.cardSize.padding;
      }
    },

    toString: function() {
      return 'Hand';
    }
  });

  function Pile(options) {
    this.init(options);
  }

  Pile.prototype = new Container();
  Pile.prototype.extend({
    calcPosition: function(options) {
      options = options || {};
    },

    toString: function() {
      return 'Pile';
    },

    deal: function(count, hands) {
      if (!this.dealCounter) {
        this.dealCounter = count * hands.length;
      }
    }
  });


  return {
    init: init,
    all: all,
    options: opt,
    SIZE: opt.cardSize,
    Card: Card,
    Container: Container,
    Deck: Deck,
    Hand: Hand,
    Pile: Pile,
  };
})();

if (typeof module !== 'undefined') {
  module.exports = cards;
}
