class Translator {
    translation = null;
    lang = null;

    constructor() {

    }

    async init() {
        let lang = window.localStorage.getItem('lang');
        if (lang === null) {
            lang = 'de';
        }
        await this.set_language(lang);
    }

    async set_language(lang = null) {
        if (lang !== null) {
            this.lang = lang;
        }
        else {
            lang = this.lang;
        }
        window.localStorage.setItem('lang', lang)
        let self = this;
        if (lang !== 'C') {
            const response = await fetch('lang/' + lang + '.json');
            if (response.status !== 200) {
                console.log('Error loading language "' + self.lang + '"');
                self.lang = 'C';
                self.translation = null;
            }
            else {
                self.translation = await response.json();
            }
        }
        else {
            this.translation = null;
        }
        self.translate_dom();
    }

    translate_dom() {
        let items = document.getElementsByTagName('my-translate');
        for (let i = 0; i < items.length; i++) {
            let item = items[i];
            let msg = item.getAttribute('msg');
            item.textContent = this.translate(msg);
        }
    }

    translate(msg) {
        if ( (this.lang === 'C') || (msg === null) ) {
            return msg;
        }
        if (msg in this.translation) {
            return this.translation[msg];
        }
        else {
            console.error("Unable to translate \"" + msg + "\"");
            return msg;
        }
    }
}