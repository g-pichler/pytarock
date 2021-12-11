function fallbackCopyURLToClipboard() {
  var textArea = document.createElement("textarea");
  textArea.value = window.location.href;

  // Avoid scrolling to bottom
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.position = "fixed";

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    var successful = document.execCommand('copy');
    var msg = successful ? 'successful' : 'unsuccessful';
    console.log('Fallback: Copying text command was ' + msg);
  } catch (err) {
    console.error('Fallback: Oops, unable to copy', err);
  }

  document.body.removeChild(textArea);
}

function copyURLToClipboard() {
  if (!navigator.clipboard) {
    fallbackCopyURLToClipboard();
    return;
  }
  navigator.clipboard.writeText(window.location.href).then(function() {
    console.log('Async: Copying to clipboard was successful!');
  }, function(err) {
    console.error('Async: Could not copy URL: ', err);
  });
}

class GameConfig {
    cookiename = "tarock_name";
    name_field = null;
    websocket = null;

    constructor(websocket, name_id = 'name', name_button_id = 'setName', gametype_button_id = 'gametypeConfirm') {
        this.name_field = document.getElementById(name_id);
        this.name_field.value = this.getName();

        this.websocket = websocket;
        var self = this;
        if (this.websocket.readyState < 1) {
            this.websocket.onopen = function () {
                self.setName()
            };
        } else {
            this.setName();
        }

        document.getElementById(name_button_id).onclick = function () {
            self.setName()
        };
        document.getElementById(gametype_button_id).onclick = function () {
            self.setGametype()
        };

        document.getElementById('autoplayButton').onclick = function () {
            self.autoplay()
        };

        document.getElementById('finishgameButton').onclick = function () {
            self.finish_game()
        };

        for (let i=0; i < 6; i++) {
            document.getElementById('points_'+i+'_A').onclick = function () {self.update_teams()};
            document.getElementById('points_'+i+'_B').onclick = function () {self.update_teams()};
        }

        document.getElementById('newGame').onclick = function () {self.new_game()};
    }

    new_game() {
        this.websocket.send(JSON.stringify({'new_game': true}));
    }

    finish_game() {
        this.websocket.send(JSON.stringify({'finish_game': true}));
    }

    update_teams() {
        let teams = [];
        for (let i=0; i < 6; i++) {
            if (document.getElementById('points_'+i+'_A').checked) {
                teams.push(0);
            }
            else
            {
                teams.push(1);
            }
        }
        this.websocket.send(JSON.stringify({'teams': teams}));
    }

    set_teams(teams) {
        for (let i=0; i < teams.length; i++) {
            if (teams[i] === 0) {
                document.getElementById('points_'+i+'_A').checked = true;
            }
            else {
                document.getElementById('points_'+i+'_B').checked = true;
            }
        }
    }

    set_stiche(stiche) {
        for (let i=0; i < stiche.length; i++) {
            document.getElementById('stiche_'+i).textContent = stiche[i];
        }
    }

    set_score(score) {
        for (let i=0; i < score.length; i++) {
            document.getElementById('points_group_'+i).textContent = score[i][0] + " " + _("Points") + ", " + score[i][1] + " " +_("Cards");
        }
    }

    set_single_score(score) {
        for (let i=0; i < score.length; i++) {
            document.getElementById('points_'+i).textContent = score[i][0] + " " + _("P") + ", " + score[i][1] + " " +_("C");
        }
    }

    autoplay() {
        this.websocket.send(JSON.stringify({'autoplay': true}))
    }

    set_gametype(gametype) {
        document.getElementById('gametype').innerText = _(gametype);
        let stichecounter_visible = gametype === 'Negative';
        let elements = document.getElementsByClassName('stichcounter');
        Array.from(elements).forEach(function (counter) {
            counter.hidden = !stichecounter_visible;
        });
    }

    setGametype() {
        let gametypes = ['positive', 'negative', 'colorgame', 'sechserdreier']
        let gametype = null;
        let ouvert = document.getElementById('ouvert').checked
        document.getElementById('ouvert').checked = false
        for (let i = 0; i < gametypes.length; i++) {
            if (document.getElementById(gametypes[i]).checked) {
                gametype = gametypes[i];
            }
        }
        this.websocket.send(JSON.stringify({'select_gametype': gametype,
        'ouvert': ouvert}))
    }

    setName() {
        let storage = window.localStorage;
        let name = this.name_field.value;
        this.websocket.send(JSON.stringify({'my_name': name}));
        storage.setItem('name', name);
    }

    getName() {
        let storage = window.localStorage;
        let name = storage.getItem('name');
        if (name === null) {
            name = GameConfig.getRandomName();
        }
        return name;
    }

    static getRandomName() {
        var animal = animal_list[Math.floor(Math.random() * animal_list.length)];
        var adjective = adjective_list[Math.floor(Math.random() * adjective_list.length)];
        return GameConfig.capitalize(adjective) + " " + animal;
    }

    static capitalize(str) {
        return str[0].toUpperCase() + str.slice(1);
    }

    errmsg(errmsg) {
        // document.getElementById('errmsg').innerText = errmsg;
        let alert_div = document.createElement('div');
        alert_div.className = 'errmsg alert alert-warning alert-dismissible fade show';
        let alert_span = document.createElement('span');
        let strong = document.createElement('strong');
        strong.innerText = _("Error: ")
        let inner_span = document.createElement('span');
        inner_span.innerText = _(errmsg);
        alert_span.appendChild(strong);
        alert_span.appendChild(inner_span);
        alert_div.appendChild(alert_span);
        let btn = document.createElement('button')
        btn.className = 'btn-close'
        btn.setAttribute('type', 'button');
        btn.setAttribute('data-bs-dismiss', "alert")
        btn.setAttribute('aria-label', "Close")
        alert_div.appendChild(btn);
        document.getElementById('errmsg_box').appendChild(alert_div);
        let bsAlert = new bootstrap.Alert(alert_div);
        setTimeout(function () { bsAlert.close(); } , 4000);
    }
}

class CardManager {
    shadowed = false;
    ws = null;
    card_collections = {};
    card_collection_names = ['player_0', 'talon_a', 'talon_b', 'played_0', 'played_1', 'played_2', 'played_3',
        'post_talon_a', 'post_talon_b', 'playerhand_1', 'playerhand_2', 'playerhand_3'];
    stage = null;
    primary = null;
    taken_collections = [];
    taken_0_colls = [];

    setup_callbacks() {
        let self = this;
        this.card_collections['talon_a'].setClick(function (card) {
            self.click_talon(0);
        });
        this.card_collections['talon_b'].setClick(function (card) {
            self.click_talon(1);
        });
        this.card_collections['player_0'].setClick(function (card) {
            self.click_card(card);
        });
    }

    click_talon(talon) {
        this.ws.send(JSON.stringify({'take_talon': talon}));
    }

    click_card(card) {
        this.ws.send(JSON.stringify({'move': card.getString()}));
    }

    ausspieler(aussp) {
        for (let i = 0; i < 4; i++) {
            if (i === aussp) {
                document.getElementById('turn' + i).classList.remove('hide');
            } else {
                document.getElementById('turn' + i).classList.add('hide');
            }
        }
    }


    constructor(ws) {
        this.ws = ws;
        for (let i = 0; i < this.card_collection_names.length; i++) {
            let name = this.card_collection_names[i]
            this.card_collections[name] = new CardCollection(name);
        }
        this.setup_callbacks();
    }

    get_card(cardstr, cls='playingcard') {
        if (cardstr !== null) {
            return new Card(cardstr.substring(0, 1), cardstr.substring(1), cls);
        } else {
            return new Card(null, 0, cls);
        }
    }

    set_card_collection(card_strings, name) {
        let coll = this.card_collections[name];

        if (this.stage === 'talon' && (name === 'talon_a' || name === 'talon_b') && (card_strings.length === 0)) {
            coll.shadow();
        } else {
            coll.wipe();
            coll.unshadow();
            for (let i = 0; i < card_strings.length; i++) {
                let card = card_strings[i];
                let c = this.get_card(card)
                coll.addCard(c);
            }
        }

        let all_full = true;
        for (let i = 0; i < 4; i++) {
            if (this.card_collections['played_' + i].empty) {
                all_full = false;
                break;
            }
        }
        if (this.shadowed ^ all_full) {
            for (let i = 0; i < 4; i++) {
                if (all_full) {
                    this.card_collections['played_' + i].shadow()
                } else {
                    this.card_collections['played_' + i].unshadow()
                }
                this.shadowed = all_full;
            }
        }

    }

    setPrimary(primary) {
        this.primary = primary;
        for (let i = 0; i < 4; i++) {
            if (i === primary) {
                document.getElementById('name' + i).classList.add('primary');
            } else {
                document.getElementById('name' + i).classList.remove('primary');
            }
        }
        document.getElementById('finishgameButton').hidden = !(primary === 0);
    }

    taken_0(cards1) {
        while (this.taken_0_colls.length > 0) {
            let coll = this.taken_0_colls.pop();
            coll.wipe();
        }
        let post_div = document.getElementById('taken_0');
        while (post_div.firstChild) {
            post_div.firstChild.remove();
        }
        let j = 0;
        for (j = 0; j < cards1.length; j++) {
            let cards = cards1[j];
            let collectionDiv = document.createElement('div');
            let post_id = 'taken_0_'+j;
            collectionDiv.id = post_id
            collectionDiv.classList.add('postcollection');
            post_div.appendChild(collectionDiv);
            let coll = new CardCollection(post_id);
            this.taken_0_colls.push(coll);
            for (let k = 0; k < cards.length; k++) {
                let card = this.get_card(cards[k]);
                coll.addCard(card);
            }
        }

    }

    taken_cards(cards2) {
        while (this.taken_collections.length > 0) {
            let coll = this.taken_collections.pop();
            coll.wipe();
        }
        for (let i = 0; i < cards2.length; i++) {
            let cards1 = cards2[i];
            let post_div = document.getElementById('post_'+i);
            while (post_div.firstChild) {
                post_div.firstChild.remove();
            }
            let j = 0;
            for (j = 0; j < cards1.length; j++) {
                let cards = cards1[j];
                let collectionDiv = document.createElement('div');
                let post_id = 'post_'+i+'_'+j;
                collectionDiv.id = post_id
                collectionDiv.classList.add('postcollection');
                post_div.appendChild(collectionDiv);
                let coll = new CardCollection(post_id);
                this.taken_collections.push(coll);
                for (let k = 0; k < cards.length; k++) {
                    let card = this.get_card(cards[k]);
                    coll.addCard(card);
                }
            }
            if (j === 0) {
                post_div.innerText = _("[nothing]")
            }
        }
    }

    async switchScene(stage) {
        if (this.stage !== null && this.stage !== 'postgame' && stage === 'postgame' && this.card_collections['player_0'].empty){
            await new Promise(r => setTimeout(r, 2000));
        }
        this.stage = stage;

        document.getElementById('gametypebox').hidden = !(stage === 'pregame' && this.primary === 0);
        document.getElementById('gametype_info').hidden = (stage === 'pregame');

        document.getElementById('talon_a').hidden = (stage === 'ingame' || stage === 'postgame');
        document.getElementById('talon_b').hidden = (stage === 'ingame' || stage === 'postgame');

        document.getElementById('gametable').hidden = (stage === 'postgame')
        document.getElementById('postgame').hidden = !(stage === 'postgame')
        document.getElementById('postgame2').hidden = !(stage === 'postgame')

        if (stage === 'postgame') {
            window.scrollTo(0,document.body.scrollHeight);
        }
    }
}

function makeid(length) {
   var result           = '';
   var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
   var charactersLength = characters.length;
   for ( var i = 0; i < length; i++ ) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
   }
   return result;
}

let cm = null;
let nc = null;

let t = new Translator();
let _ = function (msg) {return t.translate(msg); };

function preload_all_cards() {
    suits = ["H", "D", "S", "C", "T"];
    let max_rank = 8;
    for (let k=0; k<suits.length; k++) {
        suit = suits[k];
        if (suit === 'T') {
            max_rank = 22;
        } else {
            max_rank = 8;
        }
        for (let rank=1; rank <= max_rank; rank++) {
            var img=new Image();
            img.src="img/"+suit+rank+'.png';
        }
    }
}

document.addEventListener("DOMContentLoaded", async function (event) {
    //do work

    await t.init();

    table = window.location.search.substr(1);
    if (table === '') {
        window.location.search = '?' + makeid(6)
        return;
    }
    let url = null;
    if (location.hostname === 'localhost') {
        url = "ws://" + location.hostname + ":31426/tarockws/" + table
    }
    else {
        url = "wss://" + location.hostname.replace("www", "ws") + "/tarockws/" + table
    }
    var websocket = new WebSocket(url);
    var roomname_a = document.getElementById('roomname_a');
    roomname_a.textContent = table
    roomname_a.href = window.location.href;

    cm = new CardManager(websocket);
    nc = new GameConfig(websocket);

    websocket.onmessage = async function (event) {
        let data = JSON.parse(event.data);
        if ('alertmsg' in data) {
            //alert(data.alertmsg);
            nc.errmsg(data.alertmsg);
        }
        if ('primary' in data) {
            cm.setPrimary(data.primary)
        }
        for (let i = 0; i < cm.card_collection_names.length; i++) {
            let name = cm.card_collection_names[i]
            if (name in data) {
                cm.set_card_collection(data[name], name);
            }
        }
        if ('stage' in data) {
            await cm.switchScene(data.stage);
        }
        if ('player_names' in data) {
            for (let i = 0; i < data.player_names.length; i++) {
                let name = data.player_names[i];
                if (name === null) {
                    name = _("[not connected]");
                }
                document.getElementById('name' + i).innerText = name;
                document.getElementById('p_name' + i).innerText = name;
                document.getElementById('p2_name' + i).innerText = name;
            }
        }
        if ('taken_cards' in data) {
            cm.taken_cards(data.taken_cards);
        }
        if ('move' in data) {
            cm.ausspieler(data.move);
        }
        if ('teams' in data) {
            nc.set_teams(data.teams);
        }
        if ('score' in data) {
            nc.set_score(data.score);
        }
        if ('single_score' in data) {
            nc.set_single_score(data.single_score);
        }
        if ('taken_0' in data) {
            cm.taken_0(data.taken_0);
        }
        if ('gametype' in data) {
            nc.set_gametype(data.gametype);
        }
        if ('stiche' in data) {
            nc.set_stiche(data.stiche);
        }

    };

    setTimeout(preload_all_cards, 0);

});